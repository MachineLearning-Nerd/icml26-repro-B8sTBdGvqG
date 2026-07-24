"""Fail closed if regenerated Claim 3 evidence changes from the accepted run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_dir

    current_proof = load(root / "proof_certificate.json")
    frozen_proof = load(root / "prior_run_proof_certificate.json")
    current_controls = load(root / "negative_controls.json")
    frozen_controls = load(root / "prior_run_negative_controls.json")
    current_independent = load(root / "independent_checker_output.json")
    frozen_independent = load(root / "prior_run_independent_checker_output.json")
    current_verifier = load(root / "verifier_output.json")
    frozen_verifier = load(root / "prior_run_verifier_output.json")

    checks = {
        "obligation_names_stable": [
            item["name"] for item in current_proof["obligations"]
        ]
        == [item["name"] for item in frozen_proof["obligations"]],
        "all_obligations_still_pass": current_proof["all_obligations_passed"]
        and all(item["passed"] for item in current_proof["obligations"]),
        "symbolic_values_stable": current_proof["symbolic_values"]
        == frozen_proof["symbolic_values"],
        "assumptions_stable": current_proof["assumptions"]
        == frozen_proof["assumptions"],
        "negative_controls_stable": current_controls == frozen_controls,
        "independent_grid_counts_stable": (
            current_independent["rational_grid_checks"],
            current_independent["burn_in_checks"],
        )
        == (
            frozen_independent["rational_grid_checks"],
            frozen_independent["burn_in_checks"],
        ),
        "independent_checks_still_pass": current_independent["checks"]
        == frozen_independent["checks"]
        and current_independent["passed"],
        "top_level_verifier_stable": current_verifier == frozen_verifier,
    }
    passed = all(checks.values())
    output = {
        "claim_id": 3,
        "checks": checks,
        "passed": passed,
        "verdict": "VERIFIED" if passed else "BLOCKED",
    }
    print("CLAIM3_FROZEN_REGRESSION=" + json.dumps(output, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
