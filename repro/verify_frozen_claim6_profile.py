"""Verify the immutable Claim 6 CPU-calibration certificate.

This is a regression check for the accepted calibration run, not ImageNet-C
claim evidence.  The scientific verdict therefore remains BLOCKED.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EXPECTED = {
    "run_id": "f2719089-1984-45b1-b50a-1f82ec8dda9e",
    "git_sha": "26c20c77ebc3b00b10fb9e1396620247fdd1231b",
    "runtime_seconds": 1088.0,
    "model_revision": "063c6c38a5d8510b2e57df480445e94b231dad2c",
    "model_sha256": "32aa17d6e17b43500f531d5f6dc9bc93e56ed8841b8a75682e1bb295d722405b",
    "clean_revision": "55405c49dece42420e68ddd5f80174f19b29ebaf",
    "corrupt_revision": "bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7",
    "selected_rate": 15.04956307060548,
    "combined_rate": 14.643929178185857,
    "wrong_rate": 0.5298180882166253,
    "projected_seconds": 39993.42511299664,
    "safety_adjusted_seconds": 79986.85022599329,
}


def close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    profile = json.loads(
        (args.artifact_dir / "prior_run_cpu_profile.json").read_text()
    )
    anchors = profile["input_anchors"]
    model = anchors["model"]
    selected = profile["selected"]
    projection = profile["projection"]
    controls = profile["negative_controls"]
    verification = profile["verification"]

    expected_file_hashes = {
        "834de65c4e8fd824bdf621b95419d49f6ef01afced1e56d926325df49c55ba59",
        "71910a70bd5c447b84dda845a1c5f5f0a95c5daf9cf22426383e52b713eb7a57",
        "cbb300024f54900914df90b761acc3e27139acd820b74e895736953b93511b1a",
    }
    checks = {
        "identity_matches_accepted_run": (
            profile["run_id"] == EXPECTED["run_id"]
            and profile["git_sha"] == EXPECTED["git_sha"]
            and close(profile["runtime_seconds"], EXPECTED["runtime_seconds"])
        ),
        "cpu_allocation_recorded": (
            profile["expected_core_count"] == 64
            and profile["actual_cpu_allocation"]["affinity_count"] == 64
            and profile["actual_cpu_allocation"]["os_cpu_count"] == 64
        ),
        "pinned_model_matches": (
            model["revision"] == EXPECTED["model_revision"]
            and model["sha256"] == EXPECTED["model_sha256"]
            and model["bytes"] == 346_284_714
        ),
        "pinned_datasets_match": (
            anchors["clean_dataset"]["revision"] == EXPECTED["clean_revision"]
            and anchors["corruption_dataset"]["revision"]
            == EXPECTED["corrupt_revision"]
        ),
        "profile_file_hashes_match": (
            len(anchors["profile_files"]) == 3
            and {row["sha256"] for row in anchors["profile_files"]}
            == expected_file_hashes
        ),
        "fixed_profile_design_matches": (
            verification["profile_sample_images"] == 192
            and verification["profile_sample_was_formula_derived"] is False
            and verification["sweep_grid_points"] == 12
        ),
        "selected_setting_matches": (
            selected["threads"] == 8
            and selected["batch_size"] == 8
            and close(
                selected["inference_images_per_second"],
                EXPECTED["selected_rate"],
            )
            and close(
                selected["combined_images_per_second"],
                EXPECTED["combined_rate"],
            )
        ),
        "projection_matches": (
            projection["full_image_count"] == 575_000
            and projection["full_data_bytes"] == 17_243_147_240
            and close(
                projection["calibrated_total_seconds"],
                EXPECTED["projected_seconds"],
            )
            and close(
                projection["safety_adjusted_seconds"],
                EXPECTED["safety_adjusted_seconds"],
            )
            and projection["safety_factor"] == 2.0
            and projection["full_run_feasible_with_12h_timeout"] is False
        ),
        "negative_controls_detected": (
            controls["ignore_io_and_preprocessing_detected"] is True
            and controls["reverse_throughput_selection_detected"] is True
            and close(
                controls["wrong_selected_inference_images_per_second"],
                EXPECTED["wrong_rate"],
            )
            and selected["inference_images_per_second"]
            > controls["wrong_selected_inference_images_per_second"]
        ),
        "accepted_checks_passed": all(
            verification[name] is True
            for name in (
                "profile_passed",
                "independent_checker_passed",
                "verifier_passed",
                "fail_closed_passed",
            )
        ),
        "stage_does_not_overclaim": (
            profile["claim_id"] == 6
            and profile["stage"] == "cpu calibration"
            and profile["claim_verdict"] == "BLOCKED"
        ),
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": "frozen CPU-calibration regression",
        "source_run_id": profile["run_id"],
        "source_git_sha": profile["git_sha"],
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    output = args.artifact_dir / "route3_frozen_profile_verifier_output.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("CLAIM6_ROUTE3_FROZEN_PROFILE=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
