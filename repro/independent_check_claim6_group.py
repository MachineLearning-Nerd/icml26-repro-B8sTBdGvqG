"""Independent structural/arithmetic checker for Claim 6 group artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PINNED_REVISIONS = {
    "model": "063c6c38a5d8510b2e57df480445e94b231dad2c",
    "clean": "55405c49dece42420e68ddd5f80174f19b29ebaf",
    "corruption": "bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(
        (args.artifact_dir / "route3_smoke_input_manifest.json").read_text()
    )
    result = json.loads(
        (args.artifact_dir / "route3_smoke_result.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route3_smoke_controls.json").read_text()
    )
    with (args.artifact_dir / "route3_smoke_trials.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = list(csv.DictReader(source))

    observed_grid = {
        (int(row["seed"]), int(row["reference_size"])) for row in rows
    }
    expected_grid = {(seed, size) for seed in (0, 1) for size in (32, 64)}
    row_arithmetic = []
    for row in rows:
        conditional = int(row["conditional_capped_crossing"])
        standard = int(row["standard_capped_crossing"])
        horizon = int(row["horizon"])
        ratio = float(row["standard_over_conditional_ratio"])
        row_arithmetic.append(
            0 <= conditional <= horizon + 1
            and 0 <= standard <= horizon + 1
            and math.isclose(
                ratio, standard / conditional, rel_tol=1e-12, abs_tol=1e-12
            )
        )

    checks = {
        "checker_is_independent": True,
        "pinned_revisions_reconstructed": (
            manifest["model"]["revision"] == PINNED_REVISIONS["model"]
            and manifest["clean"]["revision"] == PINNED_REVISIONS["clean"]
            and manifest["corruption"]["revision"]
            == PINNED_REVISIONS["corruption"]
        ),
        "manifest_checks_pass": all(manifest["checks"].values()),
        "exact_smoke_grid": len(rows) == 4 and observed_grid == expected_grid,
        "row_arithmetic_recomputed": all(row_arithmetic),
        "scope_counts_reconstructed": (
            result["scope"]["clean_images"] == 128
            and result["scope"]["corruption_images"] == 256
            and result["paper_scope"]["corruptions"] == 15
        ),
        "controls_reconstructed": (
            controls["aligned_labels"]["labels_match"]
            and controls["rolled_corruption_labels"]["error_detected"]
            and controls["entropy_extremes"]["error_detected"]
            and controls["reversed_ratio_interpretation"]["error_detected"]
        ),
        "result_checks_pass": all(result["checks"].values()),
        "smoke_cannot_be_claim_evidence": (
            manifest["mode"] == "smoke"
            and result["stage"] == "end-to-end pipeline smoke validation"
            and result["claim_verdict"] == "BLOCKED"
        ),
    }
    passed = all(checks.values())
    output = {
        "claim_id": 6,
        "route": 3,
        "stage": "independent smoke-artifact check",
        "imports_runner_or_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route3_smoke_independent_checker.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_SMOKE_INDEPENDENT=" + json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
