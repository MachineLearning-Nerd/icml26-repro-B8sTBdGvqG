"""Final Claim 6 verifier across the four blocked routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()

    release = load(args.artifact_dir / "release_audit.json")
    figure = load(args.artifact_dir / "route2_verifier_output.json")
    stall = load(args.artifact_dir / "route3_full_reconstruction_stall.json")
    falsification = load(args.artifact_dir / "route4_falsification_attempt.json")

    checks = {
        "route1_passes_and_blocks": release["route_audit_passed"]
        and release["claim_verdict"] == "BLOCKED",
        "route2_passes_and_blocks": figure["passed"]
        and figure["claim_verdict"] == "BLOCKED",
        "route3_stall_record_passes_and_blocks": stall["passed"]
        and stall["claim_verdict"] == "BLOCKED",
        "route4_falsification_search_passes_and_blocks": falsification["passed"]
        and falsification["claim_verdict"] == "BLOCKED",
        "route4_found_no_valid_counterexample": not falsification[
            "assumption_matched_counterexample_found"
        ],
        "all_route_numbers_present": {
            release["route"],
            figure["route"],
            stall["route"],
            falsification["route"],
        }
        == {1, 2, 3, 4},
    }
    result = {
        "claim_id": 6,
        "checks": checks,
        "passed": all(checks.values()),
        "verdict": "BLOCKED",
        "confidence": "LOW",
        "reason": (
            "Claim 6 is not verified or falsified: the official data are absent, "
            "the source figure is only plotted evidence, full reconstruction "
            "stalled before inference, and the required falsification route found "
            "no valid full-scope counterexample."
        ),
    }
    (args.artifact_dir / "final_blocked_verifier_output.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_FINAL_BLOCKED_VERIFIER=" + json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
