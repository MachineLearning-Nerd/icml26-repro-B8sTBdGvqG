"""Fail-closed contract verifier for the Theorem 3.1 counterexample."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()

    raw = json.loads((args.artifact_dir / "raw_results.json").read_text())
    controls = json.loads((args.artifact_dir / "negative_controls.json").read_text())

    checks = {
        "null_is_inside_stated_any_P_domain": raw["distribution"][
            "within_stated_any_P_domain"
        ],
        "reference_is_iid_from_null": raw["distribution"]["reference_iid_from_P"],
        "stream_is_iid_from_null": raw["distribution"]["stream_iid_from_P"],
        "equation6_holds": raw["assumption_audit"]["equation6_holds"],
        "dkw_error_is_exactly_zero": raw["assumption_audit"][
            "supremum_ecdf_error"
        ]
        == 0.0,
        "equation8_crosses": raw["equation8"]["first_crossing"] > 0,
        "released_algorithm_crosses": raw["released_algorithm"]["first_crossing"]
        > 0,
        "inner_probability_exceeds_alpha": raw["theorem_comparison"][
            "actual_inner_probability"
        ]
        > raw["theorem_comparison"]["required_inner_probability_at_most"],
        "outer_probability_below_required": raw["theorem_comparison"][
            "actual_outer_probability"
        ]
        < raw["theorem_comparison"]["required_outer_probability_at_least"],
        "reverse_direction_does_not_cross": controls["reverse_direction"][
            "crossing"
        ]
        == -1,
        "randomized_tie_repair_not_deterministic": controls[
            "randomized_pit_repair"
        ]["rejection_rate"]
        < 1.0,
        "randomized_tie_repair_at_most_alpha": controls["randomized_pit_repair"][
            "rejection_rate"
        ]
        <= raw["parameters"]["alpha"],
    }
    passed = all(checks.values())
    result = {
        "claim_id": 2,
        "checks": checks,
        "passed": passed,
        "verdict": "FALSIFIED" if passed else "BLOCKED",
        "reason": "An assumption-satisfying finite witness contradicts both probability inequalities."
        if passed
        else "At least one required falsification check failed.",
    }
    output_path = args.artifact_dir / "verifier_output.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM2_VERIFIER_OUTPUT=" + json.dumps(result, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
