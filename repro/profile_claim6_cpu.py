"""Calibrate full ImageNet-C reconstruction cost on the authorized CPU flavor."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
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

PROFILE_FILES = (
    (
        "clean",
        CLEAN_REPO,
        CLEAN_REVISION,
        "data/validation-00000-of-00015.parquet",
        495_278_643,
        "834de65c4e8fd824bdf621b95419d49f6ef01afced1e56d926325df49c55ba59",
    ),
    (
        "contrast",
        CORRUPT_REPO,
        CORRUPT_REVISION,
        "data/contrast/severity_5/data-00000.parquet",
        101_318_019,
        "71910a70bd5c447b84dda845a1c5f5f0a95c5daf9cf22426383e52b713eb7a57",
    ),
    (
        "defocus_blur",
        CORRUPT_REPO,
        CORRUPT_REVISION,
        "data/defocus_blur/severity_5/data-00000.parquet",
        227_133_158,
        "cbb300024f54900914df90b761acc3e27139acd820b74e895736953b93511b1a",
    ),
)
PROFILE_IMAGES_PER_SOURCE = 64
FULL_IMAGE_COUNT = 12_500 + 15 * 37_500


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lfs_sha(sibling: Any) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    return getattr(lfs, "sha256", None) if lfs is not None else None


def build_input_manifest() -> dict[str, Any]:
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
    clean_files = [
        {
            "path": sibling.rfilename,
            "bytes": sibling.size,
            "sha256": lfs_sha(sibling),
        }
        for sibling in clean_info.siblings
        if sibling.rfilename.startswith("data/validation-")
        and sibling.rfilename.endswith(".parquet")
    ]
    corruption_files = [
        {
            "path": sibling.rfilename,
            "bytes": sibling.size,
            "sha256": lfs_sha(sibling),
        }
        for sibling in corrupt_info.siblings
        if "/severity_5/" in sibling.rfilename
        and sibling.rfilename.endswith(".parquet")
    ]
    model_sibling = next(
        sibling
        for sibling in model_info.siblings
        if sibling.rfilename == MODEL_FILE
    )
    return {
        "clean": {
            "repo": CLEAN_REPO,
            "revision": clean_info.sha,
            "files": clean_files,
            "total_bytes": sum(int(item["bytes"]) for item in clean_files),
        },
        "corrupted": {
            "repo": CORRUPT_REPO,
            "revision": corrupt_info.sha,
            "severity": 5,
            "files": corruption_files,
            "total_bytes": sum(
                int(item["bytes"]) for item in corruption_files
            ),
        },
        "model": {
            "repo": MODEL_REPO,
            "revision": model_info.sha,
            "file": MODEL_FILE,
            "bytes": model_sibling.size,
            "sha256": lfs_sha(model_sibling),
        },
    }


def download_file(
    repo: str, revision: str, filename: str, *, repo_type: str | None
) -> tuple[Path, float]:
    started = time.perf_counter()
    path = Path(
        hf_hub_download(
            repo_id=repo,
            revision=revision,
            filename=filename,
            repo_type=repo_type,
        )
    )
    return path, time.perf_counter() - started


def first_image_bytes(path: Path, count: int) -> list[bytes]:
    parquet = pq.ParquetFile(path)
    output: list[bytes] = []
    for batch in parquet.iter_batches(batch_size=count, columns=["image"]):
        for item in batch.column(0).to_pylist():
            if isinstance(item, dict) and item.get("bytes") is not None:
                output.append(item["bytes"])
            else:
                raise RuntimeError("profile Parquet image is not embedded as bytes")
            if len(output) == count:
                return output
    raise RuntimeError(f"{path} contains fewer than {count} images")


def preprocess_one(transform: Any, encoded: bytes) -> torch.Tensor:
    with Image.open(io.BytesIO(encoded)) as image:
        return transform(image.convert("RGB"))


def entropy(logits: torch.Tensor) -> torch.Tensor:
    probabilities = torch.softmax(logits, dim=1)
    return -(probabilities * torch.log(probabilities.clamp_min(1e-30))).sum(dim=1)


def run_inference(
    model: torch.nn.Module, tensors: torch.Tensor, batch_size: int
) -> tuple[np.ndarray, float]:
    outputs: list[torch.Tensor] = []
    started = time.perf_counter()
    with torch.inference_mode():
        for start in range(0, len(tensors), batch_size):
            outputs.append(entropy(model(tensors[start : start + batch_size])))
    elapsed = time.perf_counter() - started
    return torch.cat(outputs).cpu().numpy(), elapsed


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_input_manifest()
    manifest_checks = {
        "clean_revision_pinned": manifest["clean"]["revision"] == CLEAN_REVISION,
        "corrupt_revision_pinned": manifest["corrupted"]["revision"]
        == CORRUPT_REVISION,
        "model_revision_pinned": manifest["model"]["revision"] == MODEL_REVISION,
        "15_clean_shards": len(manifest["clean"]["files"]) == 15,
        "15_severity5_corruptions": len(manifest["corrupted"]["files"]) == 15,
        "model_hash_pinned": manifest["model"]["sha256"] == MODEL_SHA256,
        "model_size_pinned": manifest["model"]["bytes"] == MODEL_BYTES,
    }
    manifest["checks"] = manifest_checks
    (args.artifact_dir / "route3_input_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not all(manifest_checks.values()):
        raise SystemExit("pinned input manifest check failed")

    downloads: list[dict[str, Any]] = []
    encoded_by_source: dict[str, list[bytes]] = {}
    for source, repo, revision, filename, expected_bytes, expected_hash in PROFILE_FILES:
        path, elapsed = download_file(
            repo, revision, filename, repo_type="dataset"
        )
        observed_bytes = path.stat().st_size
        observed_hash = file_sha256(path)
        checks = {
            "size_matches": observed_bytes == expected_bytes,
            "hash_matches": observed_hash == expected_hash,
        }
        if not all(checks.values()):
            raise SystemExit(f"profile input mismatch for {source}")
        downloads.append(
            {
                "source": source,
                "path": filename,
                "bytes": observed_bytes,
                "sha256": observed_hash,
                "download_seconds": elapsed,
                "megabytes_per_second": observed_bytes / elapsed / 1_000_000,
            }
        )
        encoded_by_source[source] = first_image_bytes(
            path, PROFILE_IMAGES_PER_SOURCE
        )

    model_path, model_download_seconds = download_file(
        MODEL_REPO, MODEL_REVISION, MODEL_FILE, repo_type=None
    )
    if model_path.stat().st_size != MODEL_BYTES or file_sha256(model_path) != MODEL_SHA256:
        raise SystemExit("model checkpoint mismatch")

    model_started = time.perf_counter()
    model = timm.create_model(
        MODEL_NAME, pretrained=False, checkpoint_path=str(model_path)
    )
    model.eval()
    model_load_seconds = time.perf_counter() - model_started
    data_config = resolve_data_config(model.pretrained_cfg, model=model)
    transform = create_transform(**data_config, is_training=False)
    source_order = ("clean", "contrast", "defocus_blur")
    encoded = [
        image
        for source in source_order
        for image in encoded_by_source[source]
    ]

    preprocess_rows: list[dict[str, Any]] = []
    fastest_tensors: list[torch.Tensor] | None = None
    fastest_preprocess_rate = -1.0
    for workers in (1, 8, 16):
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            tensors = list(pool.map(lambda item: preprocess_one(transform, item), encoded))
        elapsed = time.perf_counter() - started
        rate = len(tensors) / elapsed
        preprocess_rows.append(
            {
                "workers": workers,
                "images": len(tensors),
                "seconds": elapsed,
                "images_per_second": rate,
            }
        )
        if rate > fastest_preprocess_rate:
            fastest_preprocess_rate = rate
            fastest_tensors = tensors
    if fastest_tensors is None:
        raise RuntimeError("preprocessing sweep produced no tensors")
    tensor_batch = torch.stack(fastest_tensors)

    torch.set_num_interop_threads(1)
    inference_rows: list[dict[str, Any]] = []
    reference_entropies: np.ndarray | None = None
    entropy_outputs: dict[tuple[int, int], np.ndarray] = {}
    available_cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    thread_grid = sorted({min(value, available_cpus) for value in (8, 16, 32, 64)})
    for threads in thread_grid:
        torch.set_num_threads(threads)
        for batch_size in (8, 16, 32):
            with torch.inference_mode():
                _ = model(tensor_batch[:batch_size])
            entropies, elapsed = run_inference(model, tensor_batch, batch_size)
            entropy_outputs[(threads, batch_size)] = entropies
            if reference_entropies is None:
                reference_entropies = entropies
            inference_rows.append(
                {
                    "threads": threads,
                    "batch_size": batch_size,
                    "images": len(tensor_batch),
                    "seconds": elapsed,
                    "images_per_second": len(tensor_batch) / elapsed,
                    "max_abs_entropy_delta": float(
                        np.max(np.abs(entropies - reference_entropies))
                    ),
                }
            )
    best_inference = max(inference_rows, key=lambda row: row["images_per_second"])
    best_key = (int(best_inference["threads"]), int(best_inference["batch_size"]))
    best_entropies = entropy_outputs[best_key]

    source_entropies: dict[str, dict[str, float]] = {}
    for index, source in enumerate(source_order):
        values = best_entropies[
            index * PROFILE_IMAGES_PER_SOURCE : (index + 1)
            * PROFILE_IMAGES_PER_SOURCE
        ]
        source_entropies[source] = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "standard_deviation": float(np.std(values, ddof=1)),
        }

    synthetic_logits = torch.zeros((2, 1000), dtype=torch.float32)
    synthetic_logits[1, 0] = 100.0
    entropy_controls = entropy(synthetic_logits).numpy()
    data_download_seconds = sum(row["download_seconds"] for row in downloads)
    data_download_bytes = sum(row["bytes"] for row in downloads)
    measured_download_rate = data_download_bytes / data_download_seconds
    total_data_bytes = (
        manifest["clean"]["total_bytes"] + manifest["corrupted"]["total_bytes"]
    )
    combined_image_rate = 1.0 / (
        1.0 / fastest_preprocess_rate
        + 1.0 / float(best_inference["images_per_second"])
    )
    projected_download_seconds = total_data_bytes / measured_download_rate
    projected_image_seconds = FULL_IMAGE_COUNT / combined_image_rate
    projected_total_seconds = projected_download_seconds + projected_image_seconds + 600.0
    safety_factor = 2.0

    reversed_selection = min(
        inference_rows, key=lambda row: row["images_per_second"]
    )
    inference_only_projection = (
        FULL_IMAGE_COUNT / float(best_inference["images_per_second"])
    )
    controls = {
        "reverse_throughput_selection": {
            "wrong_selected_threads": reversed_selection["threads"],
            "wrong_selected_batch_size": reversed_selection["batch_size"],
            "wrong_rate": reversed_selection["images_per_second"],
            "best_rate": best_inference["images_per_second"],
            "error_detected": reversed_selection["images_per_second"]
            < best_inference["images_per_second"],
        },
        "ignore_io_and_preprocessing": {
            "wrong_inference_only_seconds": inference_only_projection,
            "calibrated_total_seconds": projected_total_seconds,
            "error_detected": inference_only_projection < projected_total_seconds,
        },
    }
    checks = {
        "manifest_checks_pass": all(manifest_checks.values()),
        "three_profile_files_hash_match": len(downloads) == 3,
        "profile_grid_has_12_points": len(inference_rows) == 12,
        "profile_sample_is_fixed_not_formula_derived": len(encoded)
        == 3 * PROFILE_IMAGES_PER_SOURCE,
        "entropy_deterministic_across_grid": max(
            float(row["max_abs_entropy_delta"]) for row in inference_rows
        )
        < 1e-4,
        "uniform_entropy_control": math.isclose(
            float(entropy_controls[0]), math.log(1000), rel_tol=1e-6
        ),
        "peaked_entropy_control": float(entropy_controls[1]) < 1e-3,
        "both_resource_controls_detected": all(
            control["error_detected"] for control in controls.values()
        ),
        "positive_measured_rates": measured_download_rate > 0
        and fastest_preprocess_rate > 0
        and float(best_inference["images_per_second"]) > 0,
    }
    passed = all(checks.values())
    profile = {
        "claim_id": 6,
        "route": 3,
        "stage": "cpu calibration",
        "profile_sample": {
            "selection": "first 64 rows of one clean and two severity-5 corruption Parquets",
            "formula_derived": False,
            "images_per_source": PROFILE_IMAGES_PER_SOURCE,
            "total_images": len(encoded),
        },
        "model": {
            "name": MODEL_NAME,
            "repo": MODEL_REPO,
            "revision": MODEL_REVISION,
            "sha256": MODEL_SHA256,
            "download_seconds": model_download_seconds,
            "load_seconds": model_load_seconds,
            "preprocessing": data_config,
        },
        "downloads": downloads,
        "source_entropies": source_entropies,
        "entropy_controls": {
            "uniform_1000_class": float(entropy_controls[0]),
            "peaked_1000_class": float(entropy_controls[1]),
        },
        "selected": {
            "threads": best_inference["threads"],
            "batch_size": best_inference["batch_size"],
            "inference_images_per_second": best_inference["images_per_second"],
            "preprocess_images_per_second": fastest_preprocess_rate,
            "combined_images_per_second": combined_image_rate,
            "measured_data_bytes_per_second": measured_download_rate,
        },
        "projection": {
            "full_image_count": FULL_IMAGE_COUNT,
            "full_data_bytes": total_data_bytes,
            "download_seconds": projected_download_seconds,
            "preprocess_plus_inference_seconds": projected_image_seconds,
            "fixed_aggregation_allowance_seconds": 600.0,
            "calibrated_total_seconds": projected_total_seconds,
            "safety_factor": safety_factor,
            "safety_adjusted_seconds": projected_total_seconds * safety_factor,
            "full_run_feasible_with_12h_timeout": projected_total_seconds
            * safety_factor
            < 12 * 3600,
        },
        "checks": checks,
        "profile_passed": passed,
        "claim_verdict": "BLOCKED",
        "reason": "Resource calibration is not ImageNet-C claim evidence.",
        "runtime_context": {
            "expected_core_count": 64,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "os_cpu_count": os.cpu_count(),
            "affinity_count": available_cpus,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    write_rows(args.artifact_dir / "route3_preprocess_profile.csv", preprocess_rows)
    write_rows(args.artifact_dir / "route3_inference_profile.csv", inference_rows)
    (args.artifact_dir / "route3_profile_controls.json").write_text(
        json.dumps(controls, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.artifact_dir / "route3_cpu_profile.json").write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE3_CPU_PROFILE=" + json.dumps(profile, sort_keys=True))
    print("CLAIM6_ROUTE3_PROFILE_CONTROLS=" + json.dumps(controls, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
