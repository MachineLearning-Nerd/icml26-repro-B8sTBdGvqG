"""Fail-closed verifier for the Claim 6 CPU calibration stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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
    checker = json.loads(
        (args.artifact_dir / "route3_profile_independent_checker.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route3_profile_controls.json").read_text()
    )
    checks = {
        "input_manifest_passes": all(manifest["checks"].values()),
        "profile_passes": profile["profile_passed"],
        "independent_checker_passes": checker["passed"],
        "both_resource_controls_detect_errors": all(
            control["error_detected"] for control in controls.values()
        ),
        "actual_allocation_recorded": profile["runtime_context"][
            "affinity_count"
        ]
        is not None,
        "projection_has_safety_factor": profile["projection"]["safety_factor"]
        == 2.0,
        "stage_does_not_overclaim": profile["claim_verdict"]
        == checker["claim_verdict"]
        == "BLOCKED",
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": "cpu calibration",
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route3_profile_verifier_output.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE3_PROFILE_VERIFIER=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
