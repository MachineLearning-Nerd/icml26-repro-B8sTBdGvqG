#!/usr/bin/env python
"""Execute the released CPU synthetic CCTM protocol and save compact evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "upstream") not in sys.path:
    sys.path.insert(0, str(ROOT / "upstream"))

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
        "protocol": f"{n_trials}-repetition immediate N(0,1)->N(1,1), n_cal=2000, T=1000",
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


def _crossing_metrics(
    crossings: list[tuple[int, int]], *, horizon: int, shift_start: int = 0
) -> dict:
    """Summarize source-style first crossings without counting pre-shift alarms.

    The authors' delay plot discards alarms that occur before the true change
    point.  Failed or premature detections are represented by the end of the
    post-change window plus one when calculating the median detection delay.
    """
    def after_shift(crossing: int) -> int:
        return crossing if crossing >= shift_start else -1

    conditional = [after_shift(c) for c, _ in crossings]
    standard = [after_shift(s) for _, s in crossings]
    conditional_detect = np.asarray([c >= 0 for c in conditional])
    standard_detect = np.asarray([s >= 0 for s in standard])
    conditional_delay = np.asarray(
        [horizon - shift_start + 1 if c < 0 else c - shift_start for c in conditional]
    )
    standard_delay = np.asarray(
        [horizon - shift_start + 1 if s < 0 else s - shift_start for s in standard]
    )
    return {
        "conditional_detection_rate_after_shift": float(np.mean(conditional_detect)),
        "standard_detection_rate_after_shift": float(np.mean(standard_detect)),
        "conditional_median_delay_or_window": float(np.median(conditional_delay)),
        "standard_median_delay_or_window": float(np.median(standard_delay)),
        "conditional_faster": bool(np.median(conditional_delay) < np.median(standard_delay)),
        "raw_first_crossings_test_relative": crossings,
    }


def run_bias_sweep(n_trials: int) -> list[dict]:
    """Full Figure-3 left source sweep: three immediate mean-shift sizes."""
    rows = []
    for shift in (1.0, 1.5, 2.0):
        crossings = []
        for trial in range(n_trials):
            conditional, standard = normal_trial(
                trial_seed(trial, offset=int(shift * 100)),
                calibration_size=1_000,
                test_size=1_000,
                shift=shift,
            )
            assert standard is not None
            crossings.append((conditional.first_crossing, standard.first_crossing))
        rows.append(
            {
                "shift_mean": shift,
                "protocol": f"{n_trials} repetitions, N(0,1) calibration and immediate shifted stream; n_cal=1000, T=1000",
                **_crossing_metrics(crossings, horizon=1_000),
            }
        )
    return rows


def run_delayed_shift(n_trials: int) -> list[dict]:
    """Full Figure-3 middle source sweep, including T=max(delay)+500 and warm-up."""
    rows = []
    calibration_size, test_size, warmup = 1_000, 4_500, 100
    for ratio in (0.2, 0.6, 4.0):
        delay = round(ratio * calibration_size)
        crossings = []
        for trial in range(n_trials):
            conditional, standard = normal_trial(
                trial_seed(trial, offset=delay),
                calibration_size=calibration_size,
                test_size=test_size,
                shift=2.0,
                delay=delay,
                warmup=warmup,
            )
            assert standard is not None
            crossings.append((conditional.first_crossing, standard.first_crossing))
        rows.append(
            {
                "delay_ratio": ratio,
                "delay_steps": delay,
                "warmup_steps": warmup,
                "protocol": f"{n_trials} repetitions, n_cal=1000, N(0,1)->N(2,1), T=4500",
                **_crossing_metrics(crossings, horizon=test_size, shift_start=delay),
            }
        )
    return rows


def run_drift_sweep(n_trials: int) -> list[dict]:
    """Full Figure-3 right source sweep with a linearly increasing mean."""
    rows = []
    for slope in (1.5, 3.0, 5.0):
        crossings = []
        for trial in range(n_trials):
            rng = np.random.RandomState(trial_seed(trial, offset=int(slope * 10)))
            calibration = rng.normal(0.0, 1.0, 2_000)
            stream = rng.normal(0.0, 1.0, 100)
            stream += slope * np.arange(100, dtype=float) / 100
            conditional = run_conditional_ctm(calibration, stream)
            standard = run_standard_ctm(calibration, stream, rng=rng)
            crossings.append((conditional.first_crossing, standard.first_crossing))
        rows.append(
            {
                "drift_slope": slope,
                "protocol": f"{n_trials} repetitions, n_cal=2000, T=100, mean shift=slope*t/T",
                **_crossing_metrics(crossings, horizon=100),
            }
        )
    return rows


def run_clipping_sweep(n_trials: int) -> list[dict]:
    """Full Figure-5 source ablation, with immediate and delayed shifts."""
    rows = []
    for delay in (0, 800):
        for clip_c in (0.0, 0.05, 0.1, 0.2):
            crossings = []
            for trial in range(n_trials):
                conditional, _ = normal_trial(
                    trial_seed(trial, offset=int(clip_c * 1_000) + delay),
                    calibration_size=2_000,
                    test_size=1_000,
                    shift=1.0,
                    delay=delay,
                    clip_C=clip_c,
                    include_standard=False,
                )
                crossings.append((conditional.first_crossing, -1))
            metrics = _crossing_metrics(crossings, horizon=1_000, shift_start=delay)
            rows.append(
                {
                    "scenario": "immediate" if delay == 0 else "delayed_at_800",
                    "clip_C": clip_c,
                    "protocol": f"{n_trials} repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
                    "conditional_detection_rate_after_shift": metrics["conditional_detection_rate_after_shift"],
                    "conditional_median_delay_or_window": metrics["conditional_median_delay_or_window"],
                    "raw_conditional_first_crossings_test_relative": [c for c, _ in crossings],
                }
            )
    return rows


def run_ar1_sweep(n_trials: int) -> dict:
    """Full Figure-6 source setting with the supplied pairwise baseline."""
    from pairwise import PairwiseBettingContinuous

    rows = []
    for trial in range(n_trials):
        rng = np.random.RandomState(trial_seed(trial))
        calibration = rng.normal(0.0, 1.0, 1_000)
        stream = np.empty(2_000, dtype=float)
        stream[0] = rng.normal(0.0, np.sqrt(1.0 / (1.0 - 0.7**2)))
        for index in range(1, stream.size):
            stream[index] = 0.7 * stream[index - 1] + rng.normal(1.0, 1.0)
        conditional = run_conditional_ctm(calibration, stream)
        standard = run_standard_ctm(calibration, stream, rng=rng)
        pairwise = PairwiseBettingContinuous(alpha=0.05).test_exchangeability(
            stream, return_details=True, cal_samples=0
        )
        rows.append(
            {
                "conditional_first_crossing": conditional.first_crossing,
                "standard_first_crossing": standard.first_crossing,
                "pairwise_first_crossing": -1 if pairwise["stopping_time"] is None else int(pairwise["stopping_time"]),
                "pairwise_max_wealth": float(pairwise["max_wealth"]),
            }
        )

    conditional = [(row["conditional_first_crossing"], -1) for row in rows]
    standard = [(-1, row["standard_first_crossing"]) for row in rows]
    pairwise = [row["pairwise_first_crossing"] for row in rows]
    return {
        "protocol": f"{n_trials} repetitions, AR(1) a=0.7 with N(1,1) innovations; n_cal=1000, T=2000",
        "conditional": _crossing_metrics(conditional, horizon=2_000)["conditional_detection_rate_after_shift"],
        "standard": _crossing_metrics(standard, horizon=2_000)["standard_detection_rate_after_shift"],
        "pairwise_detection_rate": float(np.mean(np.asarray(pairwise) >= 0)),
        "conditional_median_crossing_or_horizon": float(
            np.median([first_crossing_or_horizon(row["conditional_first_crossing"], 2_000) for row in rows])
        ),
        "standard_median_crossing_or_horizon": float(
            np.median([first_crossing_or_horizon(row["standard_first_crossing"], 2_000) for row in rows])
        ),
        "pairwise_median_crossing_or_horizon": float(
            np.median([first_crossing_or_horizon(value, 2_000) for value in pairwise])
        ),
        "raw": rows,
    }


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
        "bias_sweep": run_bias_sweep(n_trials),
        "delayed_shift": run_delayed_shift(n_trials),
        "drift_sweep": run_drift_sweep(n_trials),
        "clipping_sweep": run_clipping_sweep(n_trials),
        "ar1_sweep": run_ar1_sweep(n_trials),
        "contamination_control": run_contamination_control(),
        "horizon_power": run_horizon_power(n_trials),
        "scope": {
            "executed": "All released synthetic notebook protocols (Figures 1, 2, 3, 5, and 6), plus an increasing-horizon power check.",
            "not_executed": "ImageNet-C, because author-required precomputed entropy arrays are not released.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")
    print(
        json.dumps(
            {
                "mode": summary["mode"],
                "primary_power": {
                    key: summary["primary_power"][key]
                    for key in (
                        "conditional_rejection_rate",
                        "standard_rejection_rate",
                        "conditional_median_crossing_or_horizon",
                        "standard_median_crossing_or_horizon",
                        "conditional_faster",
                    )
                },
                "type1_rates": [
                    {
                        "calibration_size": row["reported_calibration_size"],
                        "conditional": row["conditional_type1_rate"],
                        "naive": row["naive_fixed_reference_type1_rate"],
                    }
                    for row in summary["type1_sweep"]
                ],
                "contamination_control": summary["contamination_control"],
                "ar1": {
                    key: summary["ar1_sweep"][key]
                    for key in (
                        "conditional",
                        "standard",
                        "pairwise_detection_rate",
                        "conditional_median_crossing_or_horizon",
                        "standard_median_crossing_or_horizon",
                        "pairwise_median_crossing_or_horizon",
                    )
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
