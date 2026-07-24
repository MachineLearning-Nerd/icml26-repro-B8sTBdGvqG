"""Independently recompute Claim 6 CPU resource projections."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


CLEAN_REVISION = "55405c49dece42420e68ddd5f80174f19b29ebaf"
CORRUPT_REVISION = "bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7"
MODEL_REVISION = "063c6c38a5d8510b2e57df480445e94b231dad2c"
FULL_IMAGE_COUNT = 12_500 + 15 * 37_500


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(
        (args.artifact_dir / "route3_input_manifest.json").read_text()
    )
    profile = json.loads(
        (args.artifact_dir / "route3_cpu_profile.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route3_profile_controls.json").read_text()
    )
    inference = rows(args.artifact_dir / "route3_inference_profile.csv")
    preprocessing = rows(args.artifact_dir / "route3_preprocess_profile.csv")

    best_inference = max(inference, key=lambda row: float(row["images_per_second"]))
    best_preprocess = max(
        preprocessing, key=lambda row: float(row["images_per_second"])
    )
    selected = profile["selected"]
    combined_rate = 1.0 / (
        1.0 / float(best_inference["images_per_second"])
        + 1.0 / float(best_preprocess["images_per_second"])
    )
    download_bytes = sum(int(row["bytes"]) for row in profile["downloads"])
    download_seconds = sum(
        float(row["download_seconds"]) for row in profile["downloads"]
    )
    download_rate = download_bytes / download_seconds
    total_data_bytes = (
        manifest["clean"]["total_bytes"] + manifest["corrupted"]["total_bytes"]
    )
    projected_total = (
        total_data_bytes / download_rate
        + FULL_IMAGE_COUNT / combined_rate
        + profile["projection"]["fixed_aggregation_allowance_seconds"]
    )
    checks = {
        "claim_verdict_remains_blocked": profile["claim_verdict"] == "BLOCKED",
        "profile_passed": profile["profile_passed"],
        "pinned_revisions_reconstructed": manifest["clean"]["revision"]
        == CLEAN_REVISION
        and manifest["corrupted"]["revision"] == CORRUPT_REVISION
        and manifest["model"]["revision"] == MODEL_REVISION,
        "complete_input_counts": len(manifest["clean"]["files"]) == 15
        and len(manifest["corrupted"]["files"]) == 15,
        "sample_count_is_192": profile["profile_sample"]["total_images"] == 192,
        "sample_declared_non_formula_derived": not profile["profile_sample"][
            "formula_derived"
        ],
        "inference_grid_has_12_points": len(inference) == 12,
        "preprocess_grid_has_3_points": len(preprocessing) == 3,
        "best_inference_selection_recomputed": int(selected["threads"])
        == int(best_inference["threads"])
        and int(selected["batch_size"]) == int(best_inference["batch_size"])
        and close(
            selected["inference_images_per_second"],
            float(best_inference["images_per_second"]),
        ),
        "best_preprocess_selection_recomputed": close(
            selected["preprocess_images_per_second"],
            float(best_preprocess["images_per_second"]),
        ),
        "combined_rate_recomputed": close(
            selected["combined_images_per_second"], combined_rate
        ),
        "download_rate_recomputed": close(
            selected["measured_data_bytes_per_second"], download_rate
        ),
        "full_image_count_recomputed": profile["projection"]["full_image_count"]
        == FULL_IMAGE_COUNT,
        "projection_recomputed": close(
            profile["projection"]["calibrated_total_seconds"], projected_total
        ),
        "controls_recomputed": controls["reverse_throughput_selection"][
            "error_detected"
        ]
        and controls["ignore_io_and_preprocessing"]["error_detected"],
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": "cpu calibration",
        "independent": True,
        "imports_profiler_or_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route3_profile_independent_checker.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE3_PROFILE_INDEPENDENT=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
