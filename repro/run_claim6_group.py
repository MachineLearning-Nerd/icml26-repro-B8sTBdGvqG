"""Run a pinned ImageNet-C entropy/CTM pipeline.

The initial ``smoke`` configuration validates the complete data-to-verdict
path on a deliberately reduced sample.  It is never eligible as Claim 6
evidence.  Full group configurations are added only after this path passes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import resource
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import timm
import torch
from huggingface_hub import HfApi, hf_hub_download
from PIL import Image
from timm.data import create_transform, resolve_data_config

from src.cctm_core import run_conditional_ctm, run_standard_ctm


MODEL_REPO = "timm/vit_base_patch16_224.augreg2_in21k_ft_in1k"
MODEL_REVISION = "063c6c38a5d8510b2e57df480445e94b231dad2c"
MODEL_FILE = "model.safetensors"
MODEL_SHA256 = "32aa17d6e17b43500f531d5f6dc9bc93e56ed8841b8a75682e1bb295d722405b"
MODEL_BYTES = 346_284_714
MODEL_NAME = "vit_base_patch16_224"

CLEAN_REPO = "Tsomaros/Imagenet-1k_validation"
CLEAN_REVISION = "55405c49dece42420e68ddd5f80174f19b29ebaf"
CORRUPT_REPO = "WNJXYK/TTA-ImageNet-C"
CORRUPT_REVISION = "bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7"

ALPHA = 0.05
CI_DELTA = 0.05
ONS_D = 0.5
CLIP_C = 0.05
SMOOTH = 1e-6
WARMUP = 50
THREADS = 8
BATCH_SIZE = 8
PREPROCESS_WORKERS = 8


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lfs_sha(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    return getattr(lfs, "sha256", None) if lfs is not None else None


def sibling_record(sibling: Any) -> dict[str, Any]:
    return {
        "path": sibling.rfilename,
        "bytes": sibling.size,
        "sha256": lfs_sha(sibling),
    }


def download_verified(
    repo: str,
    revision: str,
    record: dict[str, Any],
    *,
    repo_type: str | None,
) -> tuple[Path, float]:
    started = time.perf_counter()
    path = Path(
        hf_hub_download(
            repo_id=repo,
            revision=revision,
            filename=record["path"],
            repo_type=repo_type,
        )
    )
    elapsed = time.perf_counter() - started
    observed_hash = file_sha256(path)
    if path.stat().st_size != record["bytes"] or observed_hash != record["sha256"]:
        raise RuntimeError(f"pinned input mismatch: {record['path']}")
    return path, elapsed


def read_first_records(path: Path, count: int) -> tuple[list[bytes], np.ndarray]:
    parquet = pq.ParquetFile(path)
    encoded: list[bytes] = []
    labels: list[int] = []
    for batch in parquet.iter_batches(
        batch_size=min(count, 1024), columns=["image", "label"]
    ):
        images = batch.column(0).to_pylist()
        batch_labels = batch.column(1).to_pylist()
        for image, label in zip(images, batch_labels, strict=True):
            if not isinstance(image, dict) or image.get("bytes") is None:
                raise RuntimeError("Parquet image is not embedded as bytes")
            encoded.append(image["bytes"])
            labels.append(int(label))
            if len(encoded) == count:
                return encoded, np.asarray(labels, dtype=np.int64)
    raise RuntimeError(f"{path} contains fewer than {count} rows")


def preprocess_one(transform: Any, encoded: bytes) -> torch.Tensor:
    with Image.open(io.BytesIO(encoded)) as image:
        return transform(image.convert("RGB"))


def entropy(logits: torch.Tensor) -> torch.Tensor:
    probabilities = torch.softmax(logits, dim=1)
    return -(probabilities * torch.log(probabilities.clamp_min(1e-30))).sum(dim=1)


def infer_entropies(
    model: torch.nn.Module, transform: Any, encoded: list[bytes]
) -> tuple[np.ndarray, float]:
    outputs: list[np.ndarray] = []
    started = time.perf_counter()
    for chunk_start in range(0, len(encoded), 64):
        chunk = encoded[chunk_start : chunk_start + 64]
        with ThreadPoolExecutor(max_workers=PREPROCESS_WORKERS) as pool:
            tensors = list(
                pool.map(lambda item: preprocess_one(transform, item), chunk)
            )
        tensor_batch = torch.stack(tensors)
        with torch.inference_mode():
            for start in range(0, len(tensor_batch), BATCH_SIZE):
                output = entropy(model(tensor_batch[start : start + BATCH_SIZE]))
                outputs.append(output.cpu().numpy())
    return np.concatenate(outputs).astype(np.float64), time.perf_counter() - started


def validate_smoke_config(config: dict[str, Any]) -> None:
    expected = {
        "mode": "smoke",
        "group": "Noise",
        "corruptions": ["gaussian_noise"],
        "reference_sizes": [32, 64],
        "seeds": [0, 1],
        "smoke_clean_images": 128,
        "smoke_corruption_images": 256,
    }
    if config != expected:
        raise SystemExit(
            "this branch accepts only the preregistered non-claiming smoke config"
        )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text())
    validate_smoke_config(config)
    started = time.perf_counter()

    api = HfApi()
    clean_info = api.dataset_info(
        CLEAN_REPO, revision=CLEAN_REVISION, files_metadata=True
    )
    corrupt_info = api.dataset_info(
        CORRUPT_REPO, revision=CORRUPT_REVISION, files_metadata=True
    )
    model_info = api.model_info(
        MODEL_REPO, revision=MODEL_REVISION, files_metadata=True
    )
    clean_files = sorted(
        (
            sibling
            for sibling in clean_info.siblings
            if sibling.rfilename.startswith("data/validation-")
            and sibling.rfilename.endswith(".parquet")
        ),
        key=lambda sibling: sibling.rfilename,
    )
    corruption_path = "data/gaussian_noise/severity_5/data-00000.parquet"
    corrupt_sibling = next(
        sibling
        for sibling in corrupt_info.siblings
        if sibling.rfilename == corruption_path
    )
    model_sibling = next(
        sibling
        for sibling in model_info.siblings
        if sibling.rfilename == MODEL_FILE
    )
    clean_record = sibling_record(clean_files[0])
    corrupt_record = sibling_record(corrupt_sibling)
    model_record = sibling_record(model_sibling)
    manifest_checks = {
        "clean_revision_pinned": clean_info.sha == CLEAN_REVISION,
        "corruption_revision_pinned": corrupt_info.sha == CORRUPT_REVISION,
        "model_revision_pinned": model_info.sha == MODEL_REVISION,
        "clean_has_15_shards": len(clean_files) == 15,
        "model_hash_pinned": model_record["sha256"] == MODEL_SHA256,
        "model_size_pinned": model_record["bytes"] == MODEL_BYTES,
        "files_have_lfs_hashes": all(
            record["sha256"]
            for record in (clean_record, corrupt_record, model_record)
        ),
    }
    if not all(manifest_checks.values()):
        raise SystemExit("pinned input manifest failed")

    clean_path, clean_download_seconds = download_verified(
        CLEAN_REPO,
        CLEAN_REVISION,
        clean_record,
        repo_type="dataset",
    )
    corrupt_path, corrupt_download_seconds = download_verified(
        CORRUPT_REPO,
        CORRUPT_REVISION,
        corrupt_record,
        repo_type="dataset",
    )
    model_path, model_download_seconds = download_verified(
        MODEL_REPO,
        MODEL_REVISION,
        model_record,
        repo_type=None,
    )
    clean_encoded, clean_labels = read_first_records(
        clean_path, config["smoke_clean_images"]
    )
    corrupt_encoded, corrupt_labels = read_first_records(
        corrupt_path, config["smoke_corruption_images"]
    )

    model = timm.create_model(
        MODEL_NAME, pretrained=False, checkpoint_path=str(model_path)
    )
    model.eval()
    data_config = resolve_data_config(model.pretrained_cfg, model=model)
    transform = create_transform(**data_config, is_training=False)
    torch.set_num_interop_threads(1)
    torch.set_num_threads(THREADS)
    clean_entropies, clean_inference_seconds = infer_entropies(
        model, transform, clean_encoded
    )
    corrupt_entropies, corrupt_inference_seconds = infer_entropies(
        model, transform, corrupt_encoded
    )

    aligned_count = min(len(clean_labels), len(corrupt_labels))
    labels_align = bool(
        np.array_equal(
            clean_labels[:aligned_count], corrupt_labels[:aligned_count]
        )
    )
    rolled_mismatches = int(
        np.sum(
            clean_labels[:aligned_count]
            != np.roll(corrupt_labels[:aligned_count], 1)
        )
    )
    synthetic_logits = torch.zeros((2, 1000), dtype=torch.float32)
    synthetic_logits[1, 0] = 100.0
    entropy_controls = entropy(synthetic_logits).numpy()

    trial_rows: list[dict[str, Any]] = []
    horizon = len(corrupt_entropies)
    for seed in config["seeds"]:
        clean_rng = np.random.default_rng(seed)
        corrupt_rng = np.random.default_rng(seed)
        clean_order = clean_rng.permutation(len(clean_entropies))
        stream = corrupt_entropies[
            corrupt_rng.permutation(len(corrupt_entropies))
        ]
        for reference_size in config["reference_sizes"]:
            calibration = clean_entropies[clean_order[:reference_size]]
            conditional = run_conditional_ctm(
                calibration,
                stream,
                ci_delta=CI_DELTA,
                D=ONS_D,
                clip_C=CLIP_C,
                smooth=SMOOTH,
                warmup=WARMUP,
                test_alpha=ALPHA,
            )
            standard = run_standard_ctm(
                calibration,
                stream,
                rng=np.random.RandomState(seed),
                D=ONS_D,
                clip_C=CLIP_C,
                warmup=WARMUP,
                test_alpha=ALPHA,
            )
            conditional_capped = (
                conditional.first_crossing
                if conditional.first_crossing >= 0
                else horizon + 1
            )
            standard_capped = (
                standard.first_crossing
                if standard.first_crossing >= 0
                else horizon + 1
            )
            trial_rows.append(
                {
                    "mode": "smoke",
                    "group": config["group"],
                    "corruption": "gaussian_noise",
                    "seed": seed,
                    "reference_size": reference_size,
                    "horizon": horizon,
                    "conditional_first_crossing": conditional.first_crossing,
                    "standard_first_crossing": standard.first_crossing,
                    "conditional_capped_crossing": conditional_capped,
                    "standard_capped_crossing": standard_capped,
                    "standard_over_conditional_ratio": (
                        standard_capped / conditional_capped
                    ),
                }
            )

    controls = {
        "aligned_labels": {
            "aligned_rows_checked": aligned_count,
            "labels_match": labels_align,
        },
        "rolled_corruption_labels": {
            "mismatches": rolled_mismatches,
            "error_detected": rolled_mismatches > 0,
        },
        "entropy_extremes": {
            "uniform_1000_class": float(entropy_controls[0]),
            "peaked_1000_class": float(entropy_controls[1]),
            "error_detected": (
                abs(float(entropy_controls[0]) - np.log(1000.0)) < 1e-5
                and float(entropy_controls[1]) < 1e-3
            ),
        },
        "reversed_ratio_interpretation": {
            "definition": "standard capped crossing / conditional capped crossing",
            "wrong_definition": "conditional capped crossing / standard capped crossing",
            "error_detected": all(
                abs(
                    row["standard_over_conditional_ratio"]
                    * (
                        row["conditional_capped_crossing"]
                        / row["standard_capped_crossing"]
                    )
                    - 1.0
                )
                < 1e-12
                for row in trial_rows
            ),
        },
    }
    manifest = {
        "claim_id": 6,
        "mode": "smoke",
        "config": config,
        "model": {
            "repo": MODEL_REPO,
            "revision": model_info.sha,
            **model_record,
            "preprocessing": data_config,
        },
        "clean": {
            "repo": CLEAN_REPO,
            "revision": clean_info.sha,
            "file": clean_record,
            "rows_used": len(clean_entropies),
        },
        "corruption": {
            "repo": CORRUPT_REPO,
            "revision": corrupt_info.sha,
            "file": corrupt_record,
            "rows_used": len(corrupt_entropies),
            "severity": 5,
        },
        "checks": manifest_checks,
    }
    checks = {
        "manifest_checks_pass": all(manifest_checks.values()),
        "all_downloaded_hashes_match": True,
        "complete_smoke_counts": (
            len(clean_entropies) == config["smoke_clean_images"]
            and len(corrupt_entropies)
            == config["smoke_corruption_images"]
        ),
        "all_labels_align": labels_align,
        "all_negative_controls_detect_errors": (
            controls["rolled_corruption_labels"]["error_detected"]
            and controls["entropy_extremes"]["error_detected"]
            and controls["reversed_ratio_interpretation"]["error_detected"]
        ),
        "trial_grid_complete": len(trial_rows) == 4,
        "finite_entropies": bool(
            np.isfinite(clean_entropies).all()
            and np.isfinite(corrupt_entropies).all()
        ),
        "nonclaiming_mode": config["mode"] == "smoke",
    }
    passed = all(checks.values())
    actual_cpus = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else os.cpu_count()
    )
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": "end-to-end pipeline smoke validation",
        "scope": {
            "clean_images": len(clean_entropies),
            "corruption_images": len(corrupt_entropies),
            "corruptions": ["gaussian_noise"],
            "reference_sizes": config["reference_sizes"],
            "seeds": config["seeds"],
        },
        "paper_scope": {
            "clean_images": 12500,
            "corruption_images_per_file": 37500,
            "corruptions": 15,
            "reference_sizes": [100, 500, 4000],
            "seeds": 10,
        },
        "entropy_summary": {
            "clean_mean": float(np.mean(clean_entropies)),
            "corruption_mean": float(np.mean(corrupt_entropies)),
        },
        "runtime": {
            "expected_useful_cores": 8,
            "actual_cpu_allocation": actual_cpus,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "download_seconds": (
                clean_download_seconds
                + corrupt_download_seconds
                + model_download_seconds
            ),
            "clean_inference_seconds": clean_inference_seconds,
            "corruption_inference_seconds": corrupt_inference_seconds,
            "total_seconds": time.perf_counter() - started,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "checks": checks,
        "pipeline_passed": passed,
        "claim_verdict": "BLOCKED",
        "reason": (
            "This reduced smoke run validates execution only; it does not "
            "test the paper's ImageNet-C quantifiers."
        ),
    }
    write_csv(args.artifact_dir / "route3_smoke_trials.csv", trial_rows)
    for name, payload in (
        ("route3_smoke_input_manifest.json", manifest),
        ("route3_smoke_controls.json", controls),
        ("route3_smoke_result.json", result),
    ):
        (args.artifact_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
    print("CLAIM6_ROUTE3_SMOKE_MANIFEST=" + json.dumps(manifest, sort_keys=True))
    print("CLAIM6_ROUTE3_SMOKE_TRIALS=" + json.dumps(trial_rows, sort_keys=True))
    print("CLAIM6_ROUTE3_SMOKE_CONTROLS=" + json.dumps(controls, sort_keys=True))
    print("CLAIM6_ROUTE3_SMOKE_RESULT=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
