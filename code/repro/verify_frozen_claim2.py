"""Check regenerated Claim 2 evidence against the prior immutable HF run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()

    expected = json.loads(
        (args.artifact_dir / "prior_run_raw_results.json").read_text()
    )
    actual = json.loads((args.artifact_dir / "raw_results.json").read_text())
    expected_controls = json.loads(
        (args.artifact_dir / "prior_run_negative_controls.json").read_text()
    )
    actual_controls = json.loads(
        (args.artifact_dir / "negative_controls.json").read_text()
    )

    compact_crossings = {
        str(record["seed"]): record["crossing"]
        for record in actual_controls["randomized_pit_repair"]["records"]
        if record["crossing"] >= 0
    }
    checks = {
        "equation8_crossing_stable": actual["equation8"]["first_crossing"]
        == expected["equation8"]["first_crossing"],
        "released_crossing_stable": actual["released_algorithm"]["first_crossing"]
        == expected["released_algorithm"]["first_crossing"],
        "theorem_probabilities_stable": actual["theorem_comparison"]
        == expected["theorem_comparison"],
        "assumptions_stable": actual["assumption_audit"]
        == expected["assumption_audit"],
        "reverse_control_stable": actual_controls["reverse_direction"]["crossing"]
        == expected_controls["reverse_direction"]["crossing"],
        "randomized_control_crossings_stable": compact_crossings
        == expected_controls["randomized_pit_repair"]["crossings"],
        "randomized_control_rate_stable": actual_controls[
            "randomized_pit_repair"
        ]["rejection_rate"]
        == expected_controls["randomized_pit_repair"]["rejection_rate"],
    }
    passed = all(checks.values())
    result = {
        "claim_id": 2,
        "passed": passed,
        "checks": checks,
        "verdict": "FALSIFIED" if passed else "BLOCKED",
    }
    (args.artifact_dir / "frozen_regression_output.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM2_FROZEN_REGRESSION=" + json.dumps(result, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
