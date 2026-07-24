"""Fail-closed verifier for Claim 6 smoke or full-group components."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify_full(artifact_dir: Path) -> None:
    result = json.loads(
        (artifact_dir / "route3_group_result.json").read_text()
    )
    checker = json.loads(
        (artifact_dir / "route3_group_independent_checker.json").read_text()
    )
    checks = {
        "component_passed": result["component_passed"],
        "all_component_checks_pass": all(result["checks"].values()),
        "independent_checker_passed": checker["passed"],
        "exact_full_component_scope_disclosed": (
            result["scope"]["clean_images_inferred"] == 50_000
            and result["scope"]["corruption_images_inferred_each"] == 50_000
            and len(result["scope"]["corruptions"]) >= 1
            and result["scope"]["clean_pool_size_per_seed"] == 12_500
            and result["scope"]["stream_size_per_seed"] == 37_500
            and result["scope"]["reference_sizes"]
            == [100, 250, 500, 1000, 4000]
            and result["scope"]["seeds"] == list(range(10))
            and result["scope"]["severity"] == 5
        ),
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
        "stage": result["stage"],
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (artifact_dir / "route3_group_verifier_output.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_GROUP_VERIFIER=" + json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.artifact_dir / "route3_group_result.json").exists():
        verify_full(args.artifact_dir)
        return
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
