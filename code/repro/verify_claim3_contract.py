"""Fail-closed top-level contract check for Claim 3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    proof = json.loads((args.artifact_dir / "proof_certificate.json").read_text())
    independent = json.loads(
        (args.artifact_dir / "independent_checker_output.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "negative_controls.json").read_text()
    )
    checks = {
        "corrected_proof_complete": proof["all_obligations_passed"],
        "printed_errors_detected": proof["all_negative_controls_passed"],
        "independent_checker_passes": independent["passed"],
        "asymptotic_power_obligation": next(
            item for item in proof["obligations"] if item["name"] == "asymptotic_power"
        )["passed"],
        "stopping_order_obligation": next(
            item
            for item in proof["obligations"]
            if item["name"] == "stopping_time_order"
        )["passed"],
        "two_distinct_negative_controls": len(controls) == 2,
    }
    passed = all(checks.values())
    result = {
        "claim_id": 3,
        "checks": checks,
        "passed": passed,
        "verdict": "VERIFIED" if passed else "BLOCKED",
    }
    (args.artifact_dir / "verifier_output.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM3_VERIFIER_OUTPUT=" + json.dumps(result, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
