"""Fail-closed contract verifier for Claim 6 Route 2."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def row_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as source:
        return sum(1 for _ in csv.DictReader(source))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(
        (args.artifact_dir / "route2_figure_audit.json").read_text()
    )
    checker = json.loads(
        (args.artifact_dir / "route2_independent_checker.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route2_negative_controls.json").read_text()
    )
    checks = {
        "source_figure_audit_passes": audit["route_audit_passed"],
        "independent_checker_passes": checker["passed"],
        "raw_power_rows_present": row_count(
            args.artifact_dir / "route2_power_crossings.csv"
        )
        == 21,
        "raw_ratio_rows_present": row_count(
            args.artifact_dir / "route2_ratio_points.csv"
        )
        == 20,
        "both_negative_controls_detect_errors": all(
            control["error_detected"] and not control["wrong_hypothesis_passed"]
            for control in controls.values()
        ),
        "route_does_not_overclaim": audit["claim_verdict"]
        == checker["claim_verdict"]
        == "BLOCKED",
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 2,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
        "reason": (
            "Route 2 verifies the exact content of the pinned source figure "
            "but cannot independently verify the underlying benchmark."
        ),
    }
    (args.artifact_dir / "route2_verifier_output.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE2_VERIFIER=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
