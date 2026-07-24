"""Fail-closed verifier for the non-claiming Claim 6 pipeline smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(
        (args.artifact_dir / "route3_smoke_result.json").read_text()
    )
    checker = json.loads(
        (args.artifact_dir / "route3_smoke_independent_checker.json").read_text()
    )
    checks = {
        "pipeline_passed": result["pipeline_passed"],
        "all_pipeline_checks_pass": all(result["checks"].values()),
        "independent_checker_passed": checker["passed"],
        "exact_reduced_scope_disclosed": result["scope"]
        == {
            "clean_images": 128,
            "corruption_images": 256,
            "corruptions": ["gaussian_noise"],
            "reference_sizes": [32, 64],
            "seeds": [0, 1],
        },
        "paper_scope_disclosed": result["paper_scope"]["corruptions"] == 15,
        "stage_does_not_overclaim": (
            result["claim_verdict"]
            == checker["claim_verdict"]
            == "BLOCKED"
        ),
    }
    passed = all(checks.values())
    output = {
        "claim_id": 6,
        "route": 3,
        "stage": "end-to-end pipeline smoke validation",
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route3_smoke_verifier_output.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_SMOKE_VERIFIER=" + json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
