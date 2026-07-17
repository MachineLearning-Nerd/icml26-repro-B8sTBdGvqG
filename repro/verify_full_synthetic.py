#!/usr/bin/env python
"""Independently re-aggregate the full CCTM synthetic artifact.

This verifier deliberately does not import the martingale implementation.  It
recomputes headline rates and delay medians from the saved first-crossing
records, then applies predeclared claim checks and negative-control checks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _after_shift_metrics(
    crossings: list[list[int]], *, horizon: int, shift_start: int = 0
) -> dict[str, float]:
    conditional = [c if c >= shift_start else -1 for c, _ in crossings]
    standard = [s if s >= shift_start else -1 for _, s in crossings]

    def delay(values: list[int]) -> list[int]:
        return [horizon - shift_start + 1 if value < 0 else value - shift_start for value in values]

    return {
        "conditional_rate": float(np.mean(np.asarray(conditional) >= 0)),
        "standard_rate": float(np.mean(np.asarray(standard) >= 0)),
        "conditional_median_delay": float(np.median(delay(conditional))),
        "standard_median_delay": float(np.median(delay(standard))),
    }


def _close(left: float, right: float) -> bool:
    return bool(np.isclose(left, right, rtol=0.0, atol=1e-12))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/full_synthetic_summary.json"))
    parser.add_argument("--output", type=Path, default=Path("outputs/independent_verification.json"))
    args = parser.parse_args()

    report = json.loads(args.input.read_text())
    if report["mode"] != "full-released-synthetic-protocol":
        raise ValueError("the verifier only accepts a full, not quick-smoke, artifact")

    primary = _after_shift_metrics(report["primary_power"]["raw_first_crossings"], horizon=1_000)
    primary_ok = (
        _close(primary["conditional_rate"], report["primary_power"]["conditional_rejection_rate"])
        and _close(primary["standard_rate"], report["primary_power"]["standard_rejection_rate"])
        and _close(primary["conditional_median_delay"], report["primary_power"]["conditional_median_crossing_or_horizon"])
        and _close(primary["standard_median_delay"], report["primary_power"]["standard_median_crossing_or_horizon"])
        and primary["conditional_median_delay"] < primary["standard_median_delay"]
    )

    supporting_groups = [
        ("bias_sweep", report["bias_sweep"], 1_000, lambda row: 0),
        ("delayed_shift", report["delayed_shift"], 4_500, lambda row: int(row["delay_steps"])),
        ("drift_sweep", report["drift_sweep"], 100, lambda row: 0),
    ]
    supporting_checks: dict[str, list[bool]] = {}
    for name, rows, horizon, shift_start in supporting_groups:
        checks = []
        for row in rows:
            calculated = _after_shift_metrics(
                row["raw_first_crossings_test_relative"],
                horizon=horizon,
                shift_start=shift_start(row),
            )
            checks.append(
                _close(calculated["conditional_rate"], row["conditional_detection_rate_after_shift"])
                and _close(calculated["standard_rate"], row["standard_detection_rate_after_shift"])
                and _close(calculated["conditional_median_delay"], row["conditional_median_delay_or_window"])
                and _close(calculated["standard_median_delay"], row["standard_median_delay_or_window"])
                and calculated["conditional_median_delay"] < calculated["standard_median_delay"]
            )
        supporting_checks[name] = checks

    type1 = report["type1_sweep"]
    conditional_type1 = [float(row["conditional_type1_rate"]) for row in type1]
    naive_type1 = [float(row["naive_fixed_reference_type1_rate"]) for row in type1]
    finite_validity_ok = len(type1) == 11 and max(conditional_type1) <= 0.05
    invalid_control_ok = naive_type1[0] - conditional_type1[0] >= 0.5
    horizon_ok = all(float(row["conditional_rejection_rate"]) == 1.0 for row in report["horizon_power"])
    contamination = report["contamination_control"]
    contamination_ok = bool(contamination["fixed_reference_retains_more_shift_evidence"]) and (
        float(contamination["conditional_late_mean_ecdf"])
        > float(contamination["standard_late_mean_rank_pvalue"])
    )

    c1_ok = primary_ok and all(all(values) for values in supporting_checks.values()) and contamination_ok
    c2_ok = finite_validity_ok and invalid_control_ok and horizon_ok
    checks = {
        "source_artifact_is_full": report["mode"] == "full-released-synthetic-protocol",
        "C1_primary_and_supporting_detection_checks": c1_ok,
        "C1_test_time_contamination_mechanism_control": contamination_ok,
        "C2_full_grid_finite_sample_type1_check": finite_validity_ok,
        "C2_no_DKW_negative_control_rejects_excessively": invalid_control_ok,
        "C2_increasing_horizon_power_check": horizon_ok,
    }
    if not all(checks.values()):
        raise AssertionError(json.dumps(checks, indent=2, sort_keys=True))

    result = {
        "input": str(args.input),
        "checks": checks,
        "claim_summary": {
            "C1": "verified empirically on every released synthetic shift suite and its fixed-reference mechanism control",
            "C2": "verified empirically for the released finite null grid and increasing-horizon power check; this simulation does not purport to prove the paper's asymptotic theorem",
        },
        "headline": {
            "primary": primary,
            "max_conditional_type1_rate": max(conditional_type1),
            "max_naive_type1_rate": max(naive_type1),
            "contamination_late_ecdf_gap": float(contamination["conditional_late_mean_ecdf"])
            - float(contamination["standard_late_mean_rank_pvalue"]),
        },
        "supporting_checks": supporting_checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
