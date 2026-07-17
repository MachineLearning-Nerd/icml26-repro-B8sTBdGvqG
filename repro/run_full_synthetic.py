#!/usr/bin/env python
"""Execute the released CPU synthetic CCTM protocol and save compact evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.cctm_core import normal_trial, run_conditional_ctm, run_standard_ctm


SOURCE_COMMIT = "a9feb795d9fa98cc1d0c075f8f08a5c510c7a844"


def trial_seed(trial: int, offset: int = 0, base_seed: int = 0) -> int:
    return (base_seed * 100_003 + offset * 997 + trial) & 0xFFFF_FFFF


def first_crossing_or_horizon(crossing: int, horizon: int) -> int:
    return horizon + 1 if crossing < 0 else crossing


def normal_stream(seed: int, calibration_size: int, test_size: int, shift: float, delay: int) -> tuple[np.ndarray, np.ndarray, np.random.RandomState]:
    rng = np.random.RandomState(seed)
    calibration = rng.normal(0.0, 1.0, calibration_size)
    stream = rng.normal(0.0, 1.0, test_size)
    stream[delay:] += shift
    return calibration, stream, rng


def run_primary_power(n_trials: int) -> dict:
    rows = []
    for trial in range(n_trials):
        conditional, standard = normal_trial(
            trial_seed(trial), calibration_size=2_000, test_size=1_000, shift=1.0
        )
        assert standard is not None
        rows.append((conditional.first_crossing, standard.first_crossing))
    c = np.asarray([first_crossing_or_horizon(x, 1_000) for x, _ in rows])
    s = np.asarray([first_crossing_or_horizon(x, 1_000) for _, x in rows])
    return {
        "protocol": "100-repetition immediate N(0,1)->N(1,1), n_cal=2000, T=1000",
        "conditional_rejection_rate": float(np.mean(c <= 1_000)),
        "standard_rejection_rate": float(np.mean(s <= 1_000)),
        "conditional_median_crossing_or_horizon": float(np.median(c)),
        "standard_median_crossing_or_horizon": float(np.median(s)),
        "conditional_faster": bool(np.median(c) < np.median(s)),
        "raw_first_crossings": rows,
    }


def run_type1_sweep(n_trials: int, test_size: int, calibration_sizes: list[int]) -> list[dict]:
    rows = []
    for calibration_size in calibration_sizes:
        effective_size = max(calibration_size, 10)
        conditional_rejections = 0
        naive_rejections = 0
        for trial in range(n_trials):
            seed = trial_seed(trial, offset=calibration_size)
            calibration, stream, _ = normal_stream(seed, effective_size, test_size, shift=0.0, delay=0)
            conditional = run_conditional_ctm(calibration, stream, ci_delta=0.1)
            naive = run_conditional_ctm(calibration, stream, ci_delta=1.0)
            conditional_rejections += conditional.first_crossing >= 0
            naive_rejections += naive.first_crossing >= 0
        rows.append(
            {
                "reported_calibration_size": calibration_size,
                "effective_calibration_size": effective_size,
                "conditional_type1_rate": conditional_rejections / n_trials,
                "naive_fixed_reference_type1_rate": naive_rejections / n_trials,
                "conditional_minus_nominal": conditional_rejections / n_trials - 0.05,
            }
        )
    return rows


def run_delayed_shift(n_trials: int) -> list[dict]:
    rows = []
    calibration_size = 1_000
    for ratio in (0.2, 0.6, 4.0):
        delay = round(ratio * calibration_size)
        test_size = delay + 500
        crossings = []
        for trial in range(n_trials):
            conditional, standard = normal_trial(
                trial_seed(trial, offset=delay),
                calibration_size=calibration_size,
                test_size=test_size,
                shift=2.0,
                delay=delay,
            )
            assert standard is not None
            crossings.append((conditional.first_crossing, standard.first_crossing))
        c = np.asarray([first_crossing_or_horizon(x, test_size) for x, _ in crossings])
        s = np.asarray([first_crossing_or_horizon(x, test_size) for _, x in crossings])
        rows.append(
            {
                "delay_ratio": ratio,
                "delay_steps": delay,
                "conditional_median_crossing_or_horizon": float(np.median(c)),
                "standard_median_crossing_or_horizon": float(np.median(s)),
                "conditional_faster": bool(np.median(c) < np.median(s)),
            }
        )
    return rows


def run_contamination_control() -> dict:
    """Released Figure-1 mechanism: growing reference p-values decay after shift."""
    calibration, stream, rng = normal_stream(8128, 100, 2_300, shift=0.0, delay=0)
    stream[300:] += 1.0
    conditional = run_conditional_ctm(calibration, stream)
    standard = run_standard_ctm(calibration, stream, rng=rng)
    late = slice(1_500, None)
    return {
        "protocol": "fixed N(0,1) calibration; 300 null then 2000 N(1,1) stream points",
        "conditional_late_mean_ecdf": float(np.mean(conditional.p_values[late])),
        "standard_late_mean_rank_pvalue": float(np.mean(standard.p_values[late])),
        "fixed_reference_retains_more_shift_evidence": bool(
            np.mean(conditional.p_values[late]) > np.mean(standard.p_values[late])
        ),
    }


def run_horizon_power(n_trials: int) -> list[dict]:
    rows = []
    for horizon in (100, 300, 1_000, 3_000):
        rejections = 0
        delays = []
        for trial in range(n_trials):
            conditional, _ = normal_trial(
                trial_seed(trial, offset=horizon),
                calibration_size=2_000,
                test_size=horizon,
                shift=1.0,
                include_standard=False,
            )
            rejections += conditional.first_crossing >= 0
            delays.append(first_crossing_or_horizon(conditional.first_crossing, horizon))
        rows.append(
            {
                "horizon": horizon,
                "conditional_rejection_rate": rejections / n_trials,
                "median_crossing_or_horizon": float(np.median(delays)),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/full_synthetic_summary.json"))
    parser.add_argument("--quick", action="store_true", help="small smoke run; not evidence for publication")
    args = parser.parse_args()

    if args.quick:
        n_trials, test_size, cal_sizes = 10, 2_000, [0, 500, 2_000]
    else:
        n_trials, test_size, cal_sizes = 100, 20_000, list(range(0, 5_001, 500))

    summary = {
        "source_commit": SOURCE_COMMIT,
        "mode": "quick-smoke" if args.quick else "full-released-synthetic-protocol",
        "primary_power": run_primary_power(n_trials),
        "type1_sweep": run_type1_sweep(n_trials, test_size, cal_sizes),
        "delayed_shift": run_delayed_shift(n_trials),
        "contamination_control": run_contamination_control(),
        "horizon_power": run_horizon_power(n_trials),
        "scope": {
            "executed": "All live-claim synthetic protocols from the released source.",
            "not_executed": "ImageNet-C, because author-required precomputed entropy arrays are not released.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
