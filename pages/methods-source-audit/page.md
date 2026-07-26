# Methods & source audit


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_9fc7184d5eef", "created_at": "2026-07-17T12:16:07+00:00", "title": "Faithful and independent implementation"}
-->
The pinned source constructs the conditional test from a fixed calibration empirical CDF plus a DKW band; the standard baseline uses randomized online ranks over a growing reference set. The reproduction preserves the source ONS and betting recurrences exactly, while `searchsorted` replaces a fixed-ECDF linear scan and a Fenwick tree replaces repeated online rank scans.

Five tests directly compare the clean-room computation to the pinned source: DKW band identity, conditional transitions, growing-reference randomized ranks and wealth, warm-up transitions, and an independent 12-seed primary-prefix detection check. The full artifact then stores every raw first crossing used in the reported summary, and `repro/verify_full_synthetic.py` recomputes rates and medians from those records without importing the implementation.


---
<!-- trackio-cell
{"type": "code", "id": "cell_ec473c9060a4", "created_at": "2026-07-17T12:22:09+00:00", "title": "Full released synthetic protocol", "command": ["python", "repro/run_full_synthetic.py", "--output", "outputs/full_synthetic_summary.json"], "exit_code": 0, "duration_s": 297.963}
-->
````bash
$ python repro/run_full_synthetic.py --output outputs/full_synthetic_summary.json
````

exit 0 · 298.0s


````python title=run_full_synthetic.py
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

````


````json title=full_synthetic_summary.json
{
  "ar1_sweep": {
    "conditional": 1.0,
    "conditional_median_crossing_or_horizon": 12.0,
    "pairwise_detection_rate": 0.94,
    "pairwise_median_crossing_or_horizon": 149.0,
    "protocol": "100 repetitions, AR(1) a=0.7 with N(1,1) innovations; n_cal=1000, T=2000",
    "raw": [
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 101,
        "pairwise_max_wealth": 2.6232328401885533e+31,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 1003,
        "pairwise_max_wealth": 36580534321776.35,
        "standard_first_crossing": 20
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 789,
        "pairwise_max_wealth": 1.18777497498091e+16,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 18,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 22
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 69,
        "pairwise_max_wealth": 1.4529142578731454e+26,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 35,
        "pairwise_max_wealth": 4.0779578868952165e+23,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 129,
        "pairwise_max_wealth": 2.7783526042288126e+28,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 445,
        "pairwise_max_wealth": 5.2323766516276215e+23,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 635,
        "pairwise_max_wealth": 2.722077712303951e+22,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 1937,
        "pairwise_max_wealth": 110.47296061018852,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 53,
        "pairwise_max_wealth": 1.6036869034009305e+21,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 47,
        "pairwise_max_wealth": 8.736778296588486e+24,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 53,
        "pairwise_max_wealth": 1.6946854345637697e+24,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 37,
        "pairwise_max_wealth": 1.3095064675850888e+25,
        "standard_first_crossing": 20
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 157,
        "pairwise_max_wealth": 3.7409002501009654e+18,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 43,
        "pairwise_max_wealth": 7.775139795055883e+22,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 169,
        "pairwise_max_wealth": 2.910913300637296e+34,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 39,
        "pairwise_max_wealth": 3.114585441468012e+25,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 27,
        "pairwise_max_wealth": 3.005946099528439e+27,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 169,
        "pairwise_max_wealth": 4.397749635769633e+28,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 659,
        "pairwise_max_wealth": 301302162789.78,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 83,
        "pairwise_max_wealth": 5.226140198774342e+27,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 49,
        "pairwise_max_wealth": 1.366642968269698e+22,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 17,
        "pairwise_first_crossing": 85,
        "pairwise_max_wealth": 5.729321752025255e+18,
        "standard_first_crossing": 22
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 95,
        "pairwise_max_wealth": 2.3583004995020005e+19,
        "standard_first_crossing": 24
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 135,
        "pairwise_max_wealth": 2.0304989736481564e+21,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 271,
        "pairwise_max_wealth": 1082853467730798.5,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 107,
        "pairwise_max_wealth": 29405034867193.1,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 81,
        "pairwise_max_wealth": 1.7869952277675735e+24,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 37,
        "pairwise_max_wealth": 2.68733964286892e+30,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 145,
        "pairwise_max_wealth": 3.985275252976043e+21,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 297,
        "pairwise_max_wealth": 1.3126558613206553e+26,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 93,
        "pairwise_max_wealth": 3.845958385709762e+24,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 125,
        "pairwise_max_wealth": 4.469231604397549e+30,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 97,
        "pairwise_max_wealth": 6.915437189466485e+20,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 16,
        "pairwise_first_crossing": 69,
        "pairwise_max_wealth": 5.756287487878908e+20,
        "standard_first_crossing": 21
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 47,
        "pairwise_max_wealth": 1.8379455895908966e+17,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 69,
        "pairwise_max_wealth": 4.117798671277793e+23,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 33,
        "pairwise_max_wealth": 8.785748528965919e+30,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 35,
        "pairwise_max_wealth": 2.0449216388421793e+20,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 67,
        "pairwise_max_wealth": 2.0331108098534633e+26,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 125,
        "pairwise_max_wealth": 1.0342646233697106e+21,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 1213,
        "pairwise_max_wealth": 988192.9764779188,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 283,
        "pairwise_max_wealth": 4.6143748292273693e+21,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 715,
        "pairwise_max_wealth": 2.309205374705657e+19,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 417,
        "pairwise_max_wealth": 1.0368129101239106e+16,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 233,
        "pairwise_max_wealth": 3.72806633416869e+20,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 33,
        "pairwise_max_wealth": 9.216313038692269e+16,
        "standard_first_crossing": 20
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 103,
        "pairwise_max_wealth": 26162123304.145874,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 269,
        "pairwise_max_wealth": 1.3350011766910212e+16,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 905,
        "pairwise_max_wealth": 5.180223982745772e+18,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 1093,
        "pairwise_max_wealth": 14108830318.433537,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 16,
        "pairwise_first_crossing": 297,
        "pairwise_max_wealth": 7.060133636016671e+21,
        "standard_first_crossing": 20
      },
      {
        "conditional_first_crossing": 20,
        "pairwise_first_crossing": 149,
        "pairwise_max_wealth": 3.7073144882076074e+24,
        "standard_first_crossing": 24
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 181,
        "pairwise_max_wealth": 3.401537226651897e+20,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 85,
        "pairwise_max_wealth": 215568099.36237323,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 115,
        "pairwise_max_wealth": 2.586626465735927e+24,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 423,
        "pairwise_max_wealth": 3.437559851701257e+23,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 43,
        "pairwise_max_wealth": 4.650602541299173e+20,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 55,
        "pairwise_max_wealth": 3.8428534530615026e+26,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 517,
        "pairwise_max_wealth": 1.0130327727113093e+19,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 95,
        "pairwise_max_wealth": 3504125195697451.5,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 47,
        "pairwise_max_wealth": 5.079187608660198e+24,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 215,
        "pairwise_max_wealth": 1.0195162909540959e+24,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 17,
        "pairwise_first_crossing": 473,
        "pairwise_max_wealth": 1.6324023272874408e+16,
        "standard_first_crossing": 23
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 1565,
        "pairwise_max_wealth": 56530.84884831361,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 89,
        "pairwise_max_wealth": 3.0653575256921993e+28,
        "standard_first_crossing": 20
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 111,
        "pairwise_max_wealth": 9.604767380268261e+16,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 221,
        "pairwise_max_wealth": 2.4364375733814173e+26,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 177,
        "pairwise_max_wealth": 1.0649092823607594e+25,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 307,
        "pairwise_max_wealth": 8.995836758087635e+16,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 45,
        "pairwise_max_wealth": 9.224060169428387e+29,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 57,
        "pairwise_max_wealth": 3.011686481054284e+22,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 741,
        "pairwise_max_wealth": 469352275239646.1,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 465,
        "pairwise_max_wealth": 1.988788810112499e+17,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 193,
        "pairwise_max_wealth": 1868291795805724.2,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 17,
        "pairwise_first_crossing": 51,
        "pairwise_max_wealth": 4.962020049464157e+19,
        "standard_first_crossing": 22
      },
      {
        "conditional_first_crossing": 15,
        "pairwise_first_crossing": 187,
        "pairwise_max_wealth": 9.278024771294506e+21,
        "standard_first_crossing": 23
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 243,
        "pairwise_max_wealth": 2.4036350894941432e+29,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 18,
        "pairwise_first_crossing": 51,
        "pairwise_max_wealth": 4.944754306181325e+23,
        "standard_first_crossing": 23
      },
      {
        "conditional_first_crossing": 14,
        "pairwise_first_crossing": 149,
        "pairwise_max_wealth": 4.568506313161131e+22,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 37,
        "pairwise_max_wealth": 5.564765729252707e+29,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 25,
        "pairwise_max_wealth": 2.397285862158833e+18,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 10,
        "pairwise_first_crossing": 35,
        "pairwise_max_wealth": 3.737965181585244e+22,
        "standard_first_crossing": 15
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 255,
        "pairwise_max_wealth": 8244436225653501.0,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 125,
        "pairwise_max_wealth": 1.9894822834721577e+25,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 11,
        "pairwise_first_crossing": 187,
        "pairwise_max_wealth": 1.1741860619838086e+16,
        "standard_first_crossing": 16
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 179,
        "pairwise_max_wealth": 3.740279175383411e+18,
        "standard_first_crossing": 18
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 1315,
        "pairwise_max_wealth": 370889905.3945739,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 31,
        "pairwise_max_wealth": 1562677964045040.2,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 165,
        "pairwise_max_wealth": 7.596107358649492e+21,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": 217,
        "pairwise_max_wealth": 3.9642012942370426e+20,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 12,
        "pairwise_first_crossing": -1,
        "pairwise_max_wealth": 1.0,
        "standard_first_crossing": 17
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 365,
        "pairwise_max_wealth": 1.3403042180164286e+19,
        "standard_first_crossing": 14
      },
      {
        "conditional_first_crossing": 13,
        "pairwise_first_crossing": 161,
        "pairwise_max_wealth": 7.295799224971795e+23,
        "standard_first_crossing": 19
      },
      {
        "conditional_first_crossing": 9,
        "pairwise_first_crossing": 317,
        "pairwise_max_wealth": 1.1519838042659232e+18,
        "standard_first_crossing": 14
      }
    ],
    "standard": 1.0,
    "standard_median_crossing_or_horizon": 17.0
  },
  "bias_sweep": [
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 22.5,
      "protocol": "100 repetitions, N(0,1) calibration and immediate shifted stream; n_cal=1000, T=1000",
      "raw_first_crossings_test_relative": [
        [
          27,
          32
        ],
        [
          28,
          37
        ],
        [
          16,
          23
        ],
        [
          27,
          30
        ],
        [
          36,
          40
        ],
        [
          12,
          21
        ],
        [
          28,
          36
        ],
        [
          25,
          30
        ],
        [
          17,
          27
        ],
        [
          19,
          24
        ],
        [
          25,
          28
        ],
        [
          25,
          30
        ],
        [
          17,
          23
        ],
        [
          31,
          42
        ],
        [
          17,
          27
        ],
        [
          17,
          24
        ],
        [
          24,
          29
        ],
        [
          19,
          31
        ],
        [
          21,
          26
        ],
        [
          26,
          31
        ],
        [
          15,
          23
        ],
        [
          13,
          19
        ],
        [
          22,
          30
        ],
        [
          18,
          31
        ],
        [
          16,
          24
        ],
        [
          28,
          34
        ],
        [
          22,
          28
        ],
        [
          18,
          29
        ],
        [
          32,
          38
        ],
        [
          24,
          31
        ],
        [
          27,
          31
        ],
        [
          19,
          25
        ],
        [
          14,
          23
        ],
        [
          25,
          29
        ],
        [
          21,
          29
        ],
        [
          18,
          25
        ],
        [
          30,
          45
        ],
        [
          11,
          25
        ],
        [
          25,
          30
        ],
        [
          16,
          23
        ],
        [
          17,
          22
        ],
        [
          39,
          42
        ],
        [
          29,
          36
        ],
        [
          38,
          42
        ],
        [
          34,
          38
        ],
        [
          35,
          39
        ],
        [
          39,
          43
        ],
        [
          24,
          31
        ],
        [
          35,
          40
        ],
        [
          14,
          19
        ],
        [
          28,
          35
        ],
        [
          16,
          24
        ],
        [
          23,
          36
        ],
        [
          16,
          24
        ],
        [
          16,
          25
        ],
        [
          17,
          24
        ],
        [
          31,
          35
        ],
        [
          20,
          26
        ],
        [
          20,
          26
        ],
        [
          32,
          39
        ],
        [
          12,
          23
        ],
        [
          27,
          33
        ],
        [
          11,
          20
        ],
        [
          15,
          24
        ],
        [
          15,
          22
        ],
        [
          27,
          32
        ],
        [
          16,
          25
        ],
        [
          26,
          31
        ],
        [
          13,
          29
        ],
        [
          14,
          23
        ],
        [
          23,
          29
        ],
        [
          29,
          33
        ],
        [
          38,
          56
        ],
        [
          29,
          34
        ],
        [
          27,
          31
        ],
        [
          16,
          22
        ],
        [
          31,
          40
        ],
        [
          21,
          42
        ],
        [
          24,
          33
        ],
        [
          25,
          34
        ],
        [
          24,
          36
        ],
        [
          13,
          20
        ],
        [
          39,
          42
        ],
        [
          17,
          26
        ],
        [
          31,
          36
        ],
        [
          31,
          34
        ],
        [
          12,
          26
        ],
        [
          18,
          34
        ],
        [
          32,
          37
        ],
        [
          18,
          30
        ],
        [
          29,
          48
        ],
        [
          25,
          30
        ],
        [
          13,
          20
        ],
        [
          13,
          25
        ],
        [
          19,
          26
        ],
        [
          41,
          50
        ],
        [
          22,
          26
        ],
        [
          13,
          20
        ],
        [
          16,
          28
        ],
        [
          39,
          42
        ]
      ],
      "shift_mean": 1.0,
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 30.0
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 12.0,
      "protocol": "100 repetitions, N(0,1) calibration and immediate shifted stream; n_cal=1000, T=1000",
      "raw_first_crossings_test_relative": [
        [
          15,
          21
        ],
        [
          14,
          21
        ],
        [
          15,
          21
        ],
        [
          14,
          20
        ],
        [
          11,
          20
        ],
        [
          11,
          17
        ],
        [
          15,
          21
        ],
        [
          11,
          21
        ],
        [
          20,
          28
        ],
        [
          11,
          16
        ],
        [
          12,
          20
        ],
        [
          12,
          18
        ],
        [
          22,
          27
        ],
        [
          12,
          18
        ],
        [
          11,
          18
        ],
        [
          11,
          19
        ],
        [
          12,
          17
        ],
        [
          14,
          21
        ],
        [
          13,
          20
        ],
        [
          9,
          16
        ],
        [
          12,
          19
        ],
        [
          10,
          17
        ],
        [
          13,
          19
        ],
        [
          13,
          18
        ],
        [
          15,
          20
        ],
        [
          12,
          18
        ],
        [
          11,
          19
        ],
        [
          13,
          19
        ],
        [
          13,
          21
        ],
        [
          11,
          17
        ],
        [
          14,
          20
        ],
        [
          14,
          20
        ],
        [
          14,
          25
        ],
        [
          14,
          21
        ],
        [
          11,
          19
        ],
        [
          17,
          24
        ],
        [
          18,
          24
        ],
        [
          10,
          17
        ],
        [
          26,
          30
        ],
        [
          11,
          20
        ],
        [
          13,
          21
        ],
        [
          10,
          16
        ],
        [
          11,
          18
        ],
        [
          11,
          17
        ],
        [
          12,
          18
        ],
        [
          19,
          25
        ],
        [
          11,
          16
        ],
        [
          21,
          26
        ],
        [
          10,
          18
        ],
        [
          17,
          23
        ],
        [
          10,
          17
        ],
        [
          11,
          20
        ],
        [
          13,
          18
        ],
        [
          11,
          16
        ],
        [
          12,
          19
        ],
        [
          11,
          16
        ],
        [
          12,
          19
        ],
        [
          16,
          21
        ],
        [
          11,
          16
        ],
        [
          11,
          17
        ],
        [
          11,
          18
        ],
        [
          14,
          21
        ],
        [
          12,
          19
        ],
        [
          13,
          21
        ],
        [
          12,
          18
        ],
        [
          11,
          17
        ],
        [
          12,
          22
        ],
        [
          11,
          17
        ],
        [
          10,
          15
        ],
        [
          18,
          24
        ],
        [
          12,
          22
        ],
        [
          21,
          27
        ],
        [
          19,
          25
        ],
        [
          10,
          16
        ],
        [
          10,
          16
        ],
        [
          11,
          17
        ],
        [
          10,
          18
        ],
        [
          15,
          23
        ],
        [
          11,
          20
        ],
        [
          13,
          20
        ],
        [
          16,
          20
        ],
        [
          12,
          20
        ],
        [
          18,
          23
        ],
        [
          24,
          29
        ],
        [
          17,
          24
        ],
        [
          13,
          19
        ],
        [
          13,
          20
        ],
        [
          10,
          18
        ],
        [
          17,
          22
        ],
        [
          13,
          19
        ],
        [
          12,
          19
        ],
        [
          22,
          28
        ],
        [
          17,
          22
        ],
        [
          14,
          21
        ],
        [
          10,
          24
        ],
        [
          12,
          20
        ],
        [
          11,
          17
        ],
        [
          14,
          20
        ],
        [
          14,
          22
        ],
        [
          12,
          18
        ]
      ],
      "shift_mean": 1.5,
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 20.0
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 10.0,
      "protocol": "100 repetitions, N(0,1) calibration and immediate shifted stream; n_cal=1000, T=1000",
      "raw_first_crossings_test_relative": [
        [
          10,
          16
        ],
        [
          11,
          17
        ],
        [
          15,
          20
        ],
        [
          10,
          16
        ],
        [
          11,
          16
        ],
        [
          10,
          15
        ],
        [
          10,
          16
        ],
        [
          10,
          16
        ],
        [
          10,
          15
        ],
        [
          13,
          19
        ],
        [
          11,
          16
        ],
        [
          11,
          16
        ],
        [
          9,
          15
        ],
        [
          10,
          16
        ],
        [
          13,
          18
        ],
        [
          10,
          16
        ],
        [
          13,
          19
        ],
        [
          15,
          20
        ],
        [
          10,
          17
        ],
        [
          10,
          15
        ],
        [
          10,
          16
        ],
        [
          11,
          16
        ],
        [
          11,
          17
        ],
        [
          10,
          16
        ],
        [
          10,
          16
        ],
        [
          11,
          17
        ],
        [
          13,
          17
        ],
        [
          9,
          15
        ],
        [
          10,
          15
        ],
        [
          11,
          18
        ],
        [
          10,
          16
        ],
        [
          12,
          18
        ],
        [
          12,
          17
        ],
        [
          10,
          15
        ],
        [
          10,
          15
        ],
        [
          12,
          17
        ],
        [
          10,
          15
        ],
        [
          9,
          15
        ],
        [
          10,
          15
        ],
        [
          12,
          17
        ],
        [
          10,
          16
        ],
        [
          12,
          17
        ],
        [
          10,
          15
        ],
        [
          10,
          15
        ],
        [
          12,
          17
        ],
        [
          10,
          16
        ],
        [
          13,
          18
        ],
        [
          10,
          16
        ],
        [
          12,
          17
        ],
        [
          11,
          17
        ],
        [
          11,
          18
        ],
        [
          11,
          16
        ],
        [
          9,
          15
        ],
        [
          15,
          22
        ],
        [
          11,
          17
        ],
        [
          9,
          15
        ],
        [
          10,
          20
        ],
        [
          10,
          16
        ],
        [
          13,
          19
        ],
        [
          10,
          16
        ],
        [
          9,
          16
        ],
        [
          11,
          16
        ],
        [
          11,
          16
        ],
        [
          10,
          16
        ],
        [
          10,
          16
        ],
        [
          11,
          18
        ],
        [
          10,
          16
        ],
        [
          12,
          19
        ],
        [
          10,
          16
        ],
        [
          10,
          16
        ],
        [
          10,
          15
        ],
        [
          9,
          18
        ],
        [
          10,
          16
        ],
        [
          12,
          17
        ],
        [
          10,
          17
        ],
        [
          14,
          19
        ],
        [
          12,
          18
        ],
        [
          10,
          17
        ],
        [
          11,
          16
        ],
        [
          11,
          16
        ],
        [
          11,
          17
        ],
        [
          12,
          17
        ],
        [
          12,
          19
        ],
        [
          10,
          16
        ],
        [
          10,
          15
        ],
        [
          10,
          17
        ],
        [
          10,
          16
        ],
        [
          9,
          15
        ],
        [
          11,
          18
        ],
        [
          10,
          15
        ],
        [
          9,
          15
        ],
        [
          9,
          15
        ],
        [
          11,
          18
        ],
        [
          14,
          19
        ],
        [
          9,
          15
        ],
        [
          13,
          18
        ],
        [
          14,
          18
        ],
        [
          10,
          16
        ],
        [
          12,
          18
        ],
        [
          11,
          16
        ]
      ],
      "shift_mean": 2.0,
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 16.0
    }
  ],
  "clipping_sweep": [
    {
      "clip_C": 0.0,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 21.0,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        17,
        34,
        11,
        11,
        43,
        37,
        34,
        33,
        31,
        13,
        21,
        21,
        22,
        16,
        14,
        20,
        19,
        26,
        21,
        32,
        25,
        28,
        24,
        19,
        22,
        36,
        15,
        29,
        31,
        12,
        29,
        14,
        10,
        22,
        15,
        20,
        32,
        25,
        27,
        16,
        27,
        23,
        35,
        12,
        26,
        29,
        10,
        16,
        21,
        16,
        18,
        20,
        13,
        21,
        26,
        24,
        16,
        13,
        23,
        18,
        13,
        25,
        23,
        12,
        24,
        22,
        24,
        21,
        17,
        18,
        38,
        17,
        26,
        28,
        19,
        18,
        14,
        13,
        15,
        17,
        35,
        31,
        12,
        11,
        28,
        24,
        14,
        12,
        14,
        15,
        29,
        27,
        28,
        19,
        30,
        34,
        37,
        13,
        17,
        25
      ],
      "scenario": "immediate"
    },
    {
      "clip_C": 0.05,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 20.0,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        28,
        14,
        16,
        26,
        13,
        23,
        19,
        14,
        23,
        21,
        17,
        22,
        14,
        19,
        21,
        54,
        28,
        21,
        26,
        24,
        19,
        28,
        25,
        15,
        23,
        11,
        13,
        16,
        30,
        23,
        28,
        22,
        27,
        47,
        20,
        16,
        10,
        29,
        13,
        27,
        15,
        22,
        18,
        19,
        40,
        24,
        23,
        19,
        16,
        30,
        17,
        31,
        16,
        15,
        59,
        20,
        15,
        20,
        20,
        17,
        33,
        16,
        15,
        13,
        13,
        38,
        19,
        18,
        27,
        13,
        30,
        13,
        13,
        21,
        28,
        24,
        14,
        22,
        21,
        15,
        21,
        18,
        29,
        17,
        10,
        15,
        13,
        17,
        37,
        13,
        28,
        12,
        19,
        14,
        29,
        22,
        22,
        18,
        30,
        19
      ],
      "scenario": "immediate"
    },
    {
      "clip_C": 0.1,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 22.0,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        25,
        21,
        19,
        36,
        19,
        12,
        18,
        37,
        22,
        22,
        16,
        16,
        27,
        19,
        24,
        31,
        35,
        18,
        21,
        24,
        10,
        33,
        34,
        27,
        22,
        37,
        16,
        31,
        18,
        29,
        22,
        42,
        25,
        36,
        18,
        19,
        14,
        25,
        16,
        28,
        17,
        20,
        25,
        22,
        14,
        19,
        24,
        27,
        18,
        20,
        12,
        13,
        14,
        24,
        29,
        20,
        20,
        17,
        24,
        26,
        28,
        14,
        25,
        11,
        26,
        20,
        30,
        21,
        22,
        23,
        26,
        13,
        15,
        16,
        14,
        14,
        15,
        13,
        30,
        26,
        22,
        23,
        21,
        29,
        32,
        26,
        17,
        11,
        35,
        31,
        26,
        16,
        19,
        17,
        19,
        22,
        38,
        23,
        23,
        27
      ],
      "scenario": "immediate"
    },
    {
      "clip_C": 0.2,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 21.0,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        23,
        34,
        18,
        14,
        14,
        17,
        29,
        14,
        21,
        23,
        16,
        13,
        18,
        27,
        24,
        21,
        29,
        18,
        24,
        18,
        13,
        12,
        28,
        18,
        30,
        17,
        22,
        13,
        17,
        33,
        42,
        18,
        13,
        22,
        33,
        23,
        12,
        16,
        37,
        12,
        25,
        19,
        14,
        27,
        40,
        20,
        13,
        26,
        13,
        14,
        22,
        23,
        15,
        19,
        32,
        20,
        15,
        15,
        12,
        31,
        30,
        17,
        28,
        33,
        20,
        12,
        12,
        21,
        21,
        40,
        20,
        29,
        22,
        13,
        28,
        28,
        13,
        17,
        24,
        21,
        25,
        22,
        43,
        22,
        17,
        16,
        26,
        28,
        23,
        14,
        51,
        55,
        23,
        16,
        29,
        31,
        27,
        26,
        21,
        19
      ],
      "scenario": "immediate"
    },
    {
      "clip_C": 0.0,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 100.0,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        910,
        876,
        867,
        902,
        930,
        868,
        900,
        907,
        895,
        892,
        903,
        873,
        907,
        906,
        910,
        902,
        909,
        920,
        940,
        869,
        892,
        904,
        930,
        895,
        893,
        895,
        906,
        893,
        894,
        884,
        896,
        892,
        916,
        910,
        898,
        928,
        898,
        901,
        889,
        874,
        875,
        876,
        871,
        919,
        861,
        908,
        906,
        904,
        901,
        881,
        902,
        895,
        923,
        880,
        924,
        895,
        890,
        911,
        936,
        904,
        912,
        879,
        891,
        923,
        894,
        903,
        884,
        878,
        931,
        900,
        900,
        907,
        930,
        895,
        903,
        890,
        894,
        901,
        915,
        889,
        881,
        892,
        903,
        913,
        876,
        909,
        893,
        889,
        906,
        899,
        910,
        915,
        882,
        875,
        877,
        906,
        882,
        902,
        931,
        904
      ],
      "scenario": "delayed_at_800"
    },
    {
      "clip_C": 0.05,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 98.5,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        884,
        888,
        891,
        895,
        895,
        870,
        904,
        891,
        891,
        912,
        911,
        871,
        900,
        924,
        901,
        897,
        914,
        902,
        904,
        876,
        875,
        866,
        925,
        887,
        904,
        888,
        904,
        864,
        902,
        878,
        905,
        896,
        892,
        895,
        891,
        891,
        874,
        917,
        897,
        922,
        903,
        865,
        901,
        910,
        898,
        888,
        927,
        894,
        912,
        877,
        894,
        905,
        922,
        884,
        896,
        918,
        901,
        898,
        907,
        913,
        936,
        903,
        887,
        890,
        868,
        870,
        899,
        911,
        915,
        901,
        915,
        891,
        886,
        902,
        881,
        873,
        944,
        900,
        909,
        935,
        896,
        900,
        877,
        904,
        906,
        916,
        870,
        914,
        904,
        913,
        922,
        878,
        896,
        915,
        895,
        907,
        885,
        867,
        895,
        905
      ],
      "scenario": "delayed_at_800"
    },
    {
      "clip_C": 0.1,
      "conditional_detection_rate_after_shift": 0.99,
      "conditional_median_delay_or_window": 91.5,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        864,
        889,
        881,
        893,
        888,
        885,
        931,
        933,
        879,
        849,
        916,
        902,
        896,
        902,
        894,
        925,
        902,
        878,
        32,
        867,
        917,
        906,
        877,
        899,
        890,
        885,
        904,
        888,
        898,
        908,
        870,
        895,
        884,
        886,
        887,
        886,
        877,
        862,
        879,
        871,
        871,
        874,
        884,
        897,
        874,
        887,
        921,
        900,
        891,
        893,
        865,
        901,
        913,
        896,
        885,
        872,
        896,
        889,
        915,
        875,
        897,
        909,
        910,
        890,
        907,
        917,
        905,
        893,
        878,
        919,
        888,
        880,
        886,
        912,
        906,
        909,
        894,
        899,
        908,
        886,
        892,
        879,
        900,
        886,
        870,
        914,
        876,
        923,
        907,
        886,
        923,
        891,
        909,
        900,
        891,
        869,
        916,
        886,
        888,
        888
      ],
      "scenario": "delayed_at_800"
    },
    {
      "clip_C": 0.2,
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_median_delay_or_window": 102.5,
      "protocol": "100 repetitions, n_cal=2000, T=1000, N(0,1)->N(1,1)",
      "raw_conditional_first_crossings_test_relative": [
        915,
        907,
        922,
        907,
        910,
        884,
        881,
        922,
        890,
        881,
        915,
        921,
        895,
        910,
        924,
        887,
        908,
        922,
        928,
        922,
        882,
        894,
        918,
        911,
        889,
        889,
        899,
        906,
        903,
        897,
        901,
        927,
        902,
        888,
        889,
        909,
        902,
        916,
        909,
        868,
        884,
        888,
        892,
        929,
        888,
        909,
        898,
        890,
        910,
        921,
        889,
        946,
        867,
        891,
        930,
        907,
        926,
        903,
        915,
        890,
        924,
        915,
        883,
        912,
        890,
        882,
        891,
        915,
        905,
        901,
        897,
        889,
        894,
        931,
        884,
        901,
        924,
        942,
        895,
        877,
        884,
        904,
        906,
        893,
        898,
        899,
        870,
        914,
        926,
        906,
        900,
        907,
        900,
        894,
        929,
        885,
        895,
        916,
        906,
        908
      ],
      "scenario": "delayed_at_800"
    }
  ],
  "contamination_control": {
    "conditional_late_mean_ecdf": 0.7434000000000001,
    "fixed_reference_retains_more_shift_evidence": true,
    "protocol": "fixed N(0,1) calibration; 300 null then 2000 N(1,1) stream points",
    "standard_late_mean_rank_pvalue": 0.5550927611665414
  },
  "delayed_shift": [
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 23.0,
      "delay_ratio": 0.2,
      "delay_steps": 200,
      "protocol": "100 repetitions, n_cal=1000, N(0,1)->N(2,1), T=4500",
      "raw_first_crossings_test_relative": [
        [
          227,
          235
        ],
        [
          221,
          223
        ],
        [
          222,
          222
        ],
        [
          226,
          231
        ],
        [
          221,
          223
        ],
        [
          224,
          236
        ],
        [
          228,
          238
        ],
        [
          223,
          220
        ],
        [
          225,
          227
        ],
        [
          225,
          231
        ],
        [
          225,
          234
        ],
        [
          221,
          230
        ],
        [
          225,
          238
        ],
        [
          223,
          230
        ],
        [
          217,
          214
        ],
        [
          223,
          229
        ],
        [
          222,
          226
        ],
        [
          224,
          220
        ],
        [
          226,
          228
        ],
        [
          228,
          237
        ],
        [
          219,
          229
        ],
        [
          222,
          226
        ],
        [
          224,
          235
        ],
        [
          227,
          235
        ],
        [
          228,
          220
        ],
        [
          226,
          225
        ],
        [
          223,
          227
        ],
        [
          223,
          231
        ],
        [
          224,
          232
        ],
        [
          220,
          224
        ],
        [
          215,
          211
        ],
        [
          221,
          225
        ],
        [
          221,
          223
        ],
        [
          229,
          238
        ],
        [
          218,
          214
        ],
        [
          221,
          223
        ],
        [
          223,
          227
        ],
        [
          226,
          236
        ],
        [
          234,
          244
        ],
        [
          226,
          230
        ],
        [
          228,
          238
        ],
        [
          224,
          234
        ],
        [
          217,
          220
        ],
        [
          230,
          236
        ],
        [
          221,
          232
        ],
        [
          221,
          224
        ],
        [
          220,
          227
        ],
        [
          223,
          224
        ],
        [
          225,
          234
        ],
        [
          224,
          225
        ],
        [
          221,
          218
        ],
        [
          227,
          239
        ],
        [
          222,
          221
        ],
        [
          224,
          232
        ],
        [
          223,
          234
        ],
        [
          230,
          240
        ],
        [
          212,
          208
        ],
        [
          229,
          239
        ],
        [
          223,
          225
        ],
        [
          222,
          234
        ],
        [
          224,
          227
        ],
        [
          230,
          239
        ],
        [
          222,
          222
        ],
        [
          221,
          231
        ],
        [
          225,
          222
        ],
        [
          213,
          217
        ],
        [
          221,
          234
        ],
        [
          221,
          227
        ],
        [
          224,
          233
        ],
        [
          219,
          218
        ],
        [
          224,
          228
        ],
        [
          221,
          226
        ],
        [
          210,
          209
        ],
        [
          225,
          227
        ],
        [
          224,
          227
        ],
        [
          222,
          235
        ],
        [
          225,
          233
        ],
        [
          227,
          230
        ],
        [
          228,
          241
        ],
        [
          227,
          237
        ],
        [
          231,
          242
        ],
        [
          224,
          237
        ],
        [
          218,
          221
        ],
        [
          221,
          222
        ],
        [
          224,
          228
        ],
        [
          225,
          224
        ],
        [
          222,
          222
        ],
        [
          222,
          231
        ],
        [
          224,
          225
        ],
        [
          222,
          232
        ],
        [
          222,
          225
        ],
        [
          220,
          229
        ],
        [
          228,
          239
        ],
        [
          222,
          228
        ],
        [
          222,
          233
        ],
        [
          229,
          234
        ],
        [
          230,
          239
        ],
        [
          222,
          229
        ],
        [
          222,
          223
        ],
        [
          229,
          237
        ]
      ],
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 29.0,
      "warmup_steps": 100
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 42.0,
      "delay_ratio": 0.6,
      "delay_steps": 600,
      "protocol": "100 repetitions, n_cal=1000, N(0,1)->N(2,1), T=4500",
      "raw_first_crossings_test_relative": [
        [
          634,
          649
        ],
        [
          641,
          653
        ],
        [
          636,
          653
        ],
        [
          638,
          643
        ],
        [
          640,
          648
        ],
        [
          641,
          652
        ],
        [
          645,
          648
        ],
        [
          644,
          657
        ],
        [
          647,
          655
        ],
        [
          640,
          647
        ],
        [
          643,
          643
        ],
        [
          644,
          647
        ],
        [
          640,
          642
        ],
        [
          641,
          650
        ],
        [
          642,
          658
        ],
        [
          628,
          621
        ],
        [
          644,
          653
        ],
        [
          642,
          650
        ],
        [
          638,
          631
        ],
        [
          639,
          629
        ],
        [
          640,
          633
        ],
        [
          643,
          654
        ],
        [
          634,
          644
        ],
        [
          645,
          640
        ],
        [
          643,
          660
        ],
        [
          645,
          647
        ],
        [
          642,
          650
        ],
        [
          642,
          643
        ],
        [
          641,
          638
        ],
        [
          642,
          654
        ],
        [
          644,
          657
        ],
        [
          646,
          653
        ],
        [
          641,
          645
        ],
        [
          635,
          643
        ],
        [
          634,
          643
        ],
        [
          647,
          653
        ],
        [
          645,
          649
        ],
        [
          653,
          669
        ],
        [
          651,
          648
        ],
        [
          647,
          657
        ],
        [
          650,
          652
        ],
        [
          648,
          651
        ],
        [
          635,
          643
        ],
        [
          643,
          645
        ],
        [
          643,
          656
        ],
        [
          642,
          658
        ],
        [
          642,
          658
        ],
        [
          638,
          646
        ],
        [
          643,
          662
        ],
        [
          646,
          652
        ],
        [
          649,
          665
        ],
        [
          641,
          656
        ],
        [
          640,
          652
        ],
        [
          639,
          653
        ],
        [
          638,
          646
        ],
        [
          642,
          652
        ],
        [
          643,
          650
        ],
        [
          648,
          650
        ],
        [
          642,
          644
        ],
        [
          638,
          652
        ],
        [
          634,
          645
        ],
        [
          647,
          660
        ],
        [
          641,
          651
        ],
        [
          641,
          631
        ],
        [
          645,
          661
        ],
        [
          638,
          646
        ],
        [
          641,
          645
        ],
        [
          647,
          660
        ],
        [
          641,
          659
        ],
        [
          639,
          652
        ],
        [
          642,
          655
        ],
        [
          645,
          635
        ],
        [
          639,
          652
        ],
        [
          644,
          643
        ],
        [
          650,
          659
        ],
        [
          635,
          645
        ],
        [
          644,
          653
        ],
        [
          643,
          453
        ],
        [
          642,
          662
        ],
        [
          647,
          650
        ],
        [
          644,
          654
        ],
        [
          642,
          628
        ],
        [
          641,
          648
        ],
        [
          635,
          642
        ],
        [
          642,
          647
        ],
        [
          635,
          645
        ],
        [
          640,
          641
        ],
        [
          646,
          652
        ],
        [
          644,
          655
        ],
        [
          647,
          674
        ],
        [
          635,
          629
        ],
        [
          639,
          660
        ],
        [
          639,
          650
        ],
        [
          647,
          667
        ],
        [
          637,
          647
        ],
        [
          635,
          649
        ],
        [
          634,
          636
        ],
        [
          640,
          646
        ],
        [
          638,
          644
        ],
        [
          635,
          642
        ]
      ],
      "standard_detection_rate_after_shift": 0.99,
      "standard_median_delay_or_window": 50.0,
      "warmup_steps": 100
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 121.5,
      "delay_ratio": 4.0,
      "delay_steps": 4000,
      "protocol": "100 repetitions, n_cal=1000, N(0,1)->N(2,1), T=4500",
      "raw_first_crossings_test_relative": [
        [
          4124,
          4118
        ],
        [
          4105,
          4143
        ],
        [
          4127,
          4150
        ],
        [
          4123,
          4135
        ],
        [
          4129,
          4133
        ],
        [
          4110,
          4121
        ],
        [
          4121,
          4133
        ],
        [
          4126,
          4188
        ],
        [
          4121,
          4137
        ],
        [
          4118,
          4099
        ],
        [
          4125,
          4142
        ],
        [
          4126,
          4166
        ],
        [
          4117,
          4121
        ],
        [
          4101,
          4089
        ],
        [
          4129,
          4171
        ],
        [
          4113,
          4101
        ],
        [
          4117,
          4122
        ],
        [
          4120,
          1701
        ],
        [
          4126,
          4130
        ],
        [
          4124,
          4127
        ],
        [
          4129,
          4183
        ],
        [
          4126,
          4110
        ],
        [
          4129,
          4145
        ],
        [
          4134,
          4140
        ],
        [
          4111,
          4176
        ],
        [
          4115,
          4129
        ],
        [
          4112,
          4119
        ],
        [
          4117,
          4125
        ],
        [
          4133,
          4145
        ],
        [
          4120,
          4108
        ],
        [
          4145,
          4177
        ],
        [
          4127,
          4141
        ],
        [
          4121,
          4151
        ],
        [
          4121,
          4163
        ],
        [
          4118,
          4122
        ],
        [
          4123,
          4149
        ],
        [
          4121,
          4163
        ],
        [
          4111,
          4112
        ],
        [
          4109,
          4124
        ],
        [
          4129,
          4118
        ],
        [
          4111,
          4147
        ],
        [
          4123,
          4112
        ],
        [
          4128,
          4146
        ],
        [
          4128,
          4096
        ],
        [
          4128,
          4106
        ],
        [
          4114,
          4150
        ],
        [
          4119,
          4170
        ],
        [
          4113,
          4111
        ],
        [
          4126,
          4183
        ],
        [
          4115,
          4094
        ],
        [
          4140,
          4190
        ],
        [
          4139,
          4148
        ],
        [
          4114,
          4142
        ],
        [
          4120,
          4188
        ],
        [
          4127,
          4119
        ],
        [
          4113,
          4085
        ],
        [
          4115,
          4136
        ],
        [
          4128,
          4112
        ],
        [
          4118,
          4150
        ],
        [
          4120,
          4136
        ],
        [
          4118,
          4152
        ],
        [
          4123,
          4117
        ],
        [
          4135,
          4160
        ],
        [
          4118,
          4127
        ],
        [
          4113,
          4182
        ],
        [
          4131,
          4168
        ],
        [
          4111,
          4113
        ],
        [
          4127,
          4140
        ],
        [
          4122,
          4164
        ],
        [
          4117,
          4158
        ],
        [
          4131,
          4171
        ],
        [
          4122,
          4166
        ],
        [
          4121,
          4140
        ],
        [
          4114,
          4122
        ],
        [
          4114,
          4125
        ],
        [
          4125,
          4127
        ],
        [
          4130,
          4129
        ],
        [
          4115,
          4128
        ],
        [
          4123,
          4109
        ],
        [
          4124,
          4186
        ],
        [
          4117,
          4170
        ],
        [
          4127,
          4174
        ],
        [
          4127,
          4174
        ],
        [
          4133,
          4157
        ],
        [
          4122,
          4144
        ],
        [
          4130,
          4172
        ],
        [
          4124,
          4141
        ],
        [
          4127,
          4123
        ],
        [
          4126,
          4146
        ],
        [
          4124,
          4100
        ],
        [
          4115,
          4145
        ],
        [
          4121,
          4144
        ],
        [
          4117,
          4099
        ],
        [
          4133,
          4092
        ],
        [
          4114,
          4102
        ],
        [
          4126,
          4167
        ],
        [
          4121,
          4168
        ],
        [
          4111,
          4100
        ],
        [
          4112,
          4142
        ],
        [
          4116,
          4171
        ]
      ],
      "standard_detection_rate_after_shift": 0.99,
      "standard_median_delay_or_window": 140.5,
      "warmup_steps": 100
    }
  ],
  "drift_sweep": [
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 62.5,
      "drift_slope": 1.5,
      "protocol": "100 repetitions, n_cal=2000, T=100, mean shift=slope*t/T",
      "raw_first_crossings_test_relative": [
        [
          59,
          63
        ],
        [
          49,
          54
        ],
        [
          68,
          70
        ],
        [
          61,
          66
        ],
        [
          82,
          84
        ],
        [
          68,
          70
        ],
        [
          73,
          74
        ],
        [
          66,
          73
        ],
        [
          79,
          83
        ],
        [
          44,
          54
        ],
        [
          67,
          68
        ],
        [
          84,
          85
        ],
        [
          54,
          62
        ],
        [
          80,
          82
        ],
        [
          60,
          60
        ],
        [
          74,
          77
        ],
        [
          52,
          58
        ],
        [
          58,
          63
        ],
        [
          71,
          71
        ],
        [
          69,
          71
        ],
        [
          58,
          66
        ],
        [
          45,
          53
        ],
        [
          55,
          65
        ],
        [
          61,
          65
        ],
        [
          60,
          63
        ],
        [
          63,
          63
        ],
        [
          75,
          76
        ],
        [
          39,
          49
        ],
        [
          62,
          65
        ],
        [
          66,
          69
        ],
        [
          80,
          80
        ],
        [
          72,
          74
        ],
        [
          55,
          61
        ],
        [
          73,
          74
        ],
        [
          51,
          54
        ],
        [
          49,
          63
        ],
        [
          67,
          77
        ],
        [
          40,
          61
        ],
        [
          83,
          84
        ],
        [
          74,
          75
        ],
        [
          77,
          77
        ],
        [
          46,
          55
        ],
        [
          72,
          74
        ],
        [
          56,
          58
        ],
        [
          62,
          64
        ],
        [
          51,
          57
        ],
        [
          75,
          77
        ],
        [
          79,
          81
        ],
        [
          63,
          65
        ],
        [
          51,
          54
        ],
        [
          73,
          74
        ],
        [
          52,
          64
        ],
        [
          48,
          52
        ],
        [
          76,
          81
        ],
        [
          53,
          61
        ],
        [
          71,
          77
        ],
        [
          71,
          74
        ],
        [
          39,
          47
        ],
        [
          75,
          77
        ],
        [
          52,
          61
        ],
        [
          65,
          68
        ],
        [
          86,
          91
        ],
        [
          56,
          59
        ],
        [
          73,
          73
        ],
        [
          71,
          74
        ],
        [
          62,
          66
        ],
        [
          60,
          63
        ],
        [
          69,
          70
        ],
        [
          62,
          64
        ],
        [
          56,
          62
        ],
        [
          69,
          75
        ],
        [
          76,
          81
        ],
        [
          63,
          64
        ],
        [
          56,
          61
        ],
        [
          57,
          58
        ],
        [
          52,
          55
        ],
        [
          66,
          70
        ],
        [
          67,
          69
        ],
        [
          69,
          69
        ],
        [
          56,
          60
        ],
        [
          60,
          71
        ],
        [
          56,
          60
        ],
        [
          57,
          60
        ],
        [
          77,
          81
        ],
        [
          53,
          57
        ],
        [
          70,
          79
        ],
        [
          66,
          68
        ],
        [
          67,
          73
        ],
        [
          56,
          61
        ],
        [
          52,
          56
        ],
        [
          62,
          64
        ],
        [
          42,
          53
        ],
        [
          68,
          70
        ],
        [
          65,
          75
        ],
        [
          52,
          63
        ],
        [
          65,
          68
        ],
        [
          34,
          42
        ],
        [
          55,
          57
        ],
        [
          70,
          73
        ],
        [
          61,
          76
        ]
      ],
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 66.0
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 42.0,
      "drift_slope": 3.0,
      "protocol": "100 repetitions, n_cal=2000, T=100, mean shift=slope*t/T",
      "raw_first_crossings_test_relative": [
        [
          36,
          41
        ],
        [
          47,
          52
        ],
        [
          39,
          43
        ],
        [
          46,
          48
        ],
        [
          37,
          40
        ],
        [
          39,
          42
        ],
        [
          32,
          39
        ],
        [
          44,
          46
        ],
        [
          41,
          49
        ],
        [
          35,
          47
        ],
        [
          54,
          57
        ],
        [
          47,
          50
        ],
        [
          32,
          40
        ],
        [
          42,
          49
        ],
        [
          27,
          34
        ],
        [
          49,
          52
        ],
        [
          46,
          50
        ],
        [
          52,
          55
        ],
        [
          48,
          51
        ],
        [
          44,
          48
        ],
        [
          47,
          50
        ],
        [
          41,
          46
        ],
        [
          44,
          48
        ],
        [
          36,
          40
        ],
        [
          54,
          58
        ],
        [
          42,
          45
        ],
        [
          36,
          39
        ],
        [
          56,
          58
        ],
        [
          34,
          38
        ],
        [
          44,
          48
        ],
        [
          48,
          52
        ],
        [
          32,
          39
        ],
        [
          39,
          42
        ],
        [
          46,
          52
        ],
        [
          40,
          44
        ],
        [
          42,
          46
        ],
        [
          26,
          33
        ],
        [
          46,
          49
        ],
        [
          45,
          47
        ],
        [
          47,
          51
        ],
        [
          35,
          42
        ],
        [
          35,
          42
        ],
        [
          43,
          47
        ],
        [
          46,
          49
        ],
        [
          41,
          48
        ],
        [
          45,
          49
        ],
        [
          37,
          41
        ],
        [
          38,
          43
        ],
        [
          43,
          46
        ],
        [
          33,
          37
        ],
        [
          39,
          46
        ],
        [
          34,
          38
        ],
        [
          42,
          48
        ],
        [
          47,
          54
        ],
        [
          51,
          56
        ],
        [
          23,
          29
        ],
        [
          44,
          48
        ],
        [
          48,
          55
        ],
        [
          32,
          42
        ],
        [
          35,
          40
        ],
        [
          43,
          48
        ],
        [
          39,
          42
        ],
        [
          38,
          42
        ],
        [
          47,
          50
        ],
        [
          39,
          46
        ],
        [
          45,
          49
        ],
        [
          40,
          46
        ],
        [
          41,
          46
        ],
        [
          40,
          45
        ],
        [
          44,
          47
        ],
        [
          41,
          47
        ],
        [
          26,
          34
        ],
        [
          40,
          45
        ],
        [
          39,
          44
        ],
        [
          31,
          36
        ],
        [
          50,
          53
        ],
        [
          41,
          44
        ],
        [
          48,
          51
        ],
        [
          43,
          48
        ],
        [
          41,
          46
        ],
        [
          34,
          43
        ],
        [
          34,
          43
        ],
        [
          35,
          46
        ],
        [
          39,
          43
        ],
        [
          29,
          34
        ],
        [
          48,
          52
        ],
        [
          51,
          53
        ],
        [
          42,
          45
        ],
        [
          44,
          47
        ],
        [
          44,
          47
        ],
        [
          31,
          38
        ],
        [
          38,
          42
        ],
        [
          38,
          43
        ],
        [
          56,
          58
        ],
        [
          50,
          53
        ],
        [
          42,
          45
        ],
        [
          43,
          47
        ],
        [
          45,
          49
        ],
        [
          42,
          46
        ],
        [
          55,
          58
        ]
      ],
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 46.0
    },
    {
      "conditional_detection_rate_after_shift": 1.0,
      "conditional_faster": true,
      "conditional_median_delay_or_window": 32.0,
      "drift_slope": 5.0,
      "protocol": "100 repetitions, n_cal=2000, T=100, mean shift=slope*t/T",
      "raw_first_crossings_test_relative": [
        [
          39,
          42
        ],
        [
          38,
          41
        ],
        [
          32,
          36
        ],
        [
          31,
          36
        ],
        [
          30,
          34
        ],
        [
          28,
          33
        ],
        [
          34,
          38
        ],
        [
          26,
          32
        ],
        [
          32,
          36
        ],
        [
          28,
          34
        ],
        [
          29,
          33
        ],
        [
          31,
          39
        ],
        [
          23,
          27
        ],
        [
          33,
          37
        ],
        [
          33,
          37
        ],
        [
          42,
          45
        ],
        [
          38,
          41
        ],
        [
          34,
          38
        ],
        [
          33,
          39
        ],
        [
          34,
          39
        ],
        [
          34,
          40
        ],
        [
          33,
          38
        ],
        [
          34,
          39
        ],
        [
          31,
          35
        ],
        [
          29,
          33
        ],
        [
          19,
          27
        ],
        [
          38,
          42
        ],
        [
          38,
          42
        ],
        [
          34,
          38
        ],
        [
          38,
          42
        ],
        [
          32,
          37
        ],
        [
          26,
          31
        ],
        [
          34,
          39
        ],
        [
          45,
          48
        ],
        [
          27,
          31
        ],
        [
          31,
          36
        ],
        [
          26,
          32
        ],
        [
          37,
          40
        ],
        [
          27,
          35
        ],
        [
          37,
          41
        ],
        [
          34,
          37
        ],
        [
          30,
          34
        ],
        [
          26,
          30
        ],
        [
          28,
          32
        ],
        [
          42,
          45
        ],
        [
          33,
          39
        ],
        [
          30,
          37
        ],
        [
          28,
          35
        ],
        [
          27,
          32
        ],
        [
          35,
          39
        ],
        [
          27,
          31
        ],
        [
          37,
          40
        ],
        [
          29,
          35
        ],
        [
          30,
          36
        ],
        [
          45,
          50
        ],
        [
          33,
          39
        ],
        [
          29,
          35
        ],
        [
          25,
          31
        ],
        [
          40,
          43
        ],
        [
          29,
          33
        ],
        [
          38,
          42
        ],
        [
          22,
          27
        ],
        [
          30,
          36
        ],
        [
          23,
          28
        ],
        [
          31,
          35
        ],
        [
          36,
          40
        ],
        [
          41,
          44
        ],
        [
          26,
          32
        ],
        [
          32,
          38
        ],
        [
          29,
          36
        ],
        [
          33,
          37
        ],
        [
          35,
          38
        ],
        [
          33,
          37
        ],
        [
          32,
          36
        ],
        [
          36,
          40
        ],
        [
          34,
          38
        ],
        [
          29,
          36
        ],
        [
          34,
          39
        ],
        [
          35,
          39
        ],
        [
          29,
          37
        ],
        [
          36,
          39
        ],
        [
          30,
          35
        ],
        [
          38,
          44
        ],
        [
          31,
          36
        ],
        [
          17,
          24
        ],
        [
          33,
          37
        ],
        [
          21,
          30
        ],
        [
          36,
          40
        ],
        [
          40,
          43
        ],
        [
          26,
          31
        ],
        [
          36,
          40
        ],
        [
          27,
          38
        ],
        [
          30,
          35
        ],
        [
          23,
          32
        ],
        [
          38,
          41
        ],
        [
          29,
          34
        ],
        [
          30,
          35
        ],
        [
          34,
          39
        ],
        [
          37,
          40
        ],
        [
          31,
          35
        ]
      ],
      "standard_detection_rate_after_shift": 1.0,
      "standard_median_delay_or_window": 37.0
    }
  ],
  "horizon_power": [
    {
      "conditional_rejection_rate": 1.0,
      "horizon": 100,
      "median_crossing_or_horizon": 22.0
    },
    {
      "conditional_rejection_rate": 1.0,
      "horizon": 300,
      "median_crossing_or_horizon": 18.0
    },
    {
      "conditional_rejection_rate": 1.0,
      "horizon": 1000,
      "median_crossing_or_horizon": 20.0
    },
    {
      "conditional_rejection_rate": 1.0,
      "horizon": 3000,
      "median_crossing_or_horizon": 21.0
    }
  ],
  "mode": "full-released-synthetic-protocol",
  "primary_power": {
    "conditional_faster": true,
    "conditional_median_crossing_or_horizon": 21.0,
    "conditional_rejection_rate": 1.0,
    "protocol": "100-repetition immediate N(0,1)->N(1,1), n_cal=2000, T=1000",
    "raw_first_crossings": [
      [
        17,
        31
      ],
      [
        35,
        40
      ],
      [
        11,
        17
      ],
      [
        11,
        21
      ],
      [
        43,
        47
      ],
      [
        37,
        47
      ],
      [
        34,
        39
      ],
      [
        33,
        43
      ],
      [
        31,
        39
      ],
      [
        13,
        20
      ],
      [
        21,
        29
      ],
      [
        21,
        30
      ],
      [
        22,
        27
      ],
      [
        16,
        27
      ],
      [
        14,
        24
      ],
      [
        20,
        28
      ],
      [
        19,
        25
      ],
      [
        26,
        33
      ],
      [
        21,
        32
      ],
      [
        30,
        38
      ],
      [
        25,
        41
      ],
      [
        28,
        34
      ],
      [
        24,
        30
      ],
      [
        19,
        24
      ],
      [
        22,
        37
      ],
      [
        36,
        40
      ],
      [
        15,
        23
      ],
      [
        29,
        34
      ],
      [
        32,
        37
      ],
      [
        12,
        20
      ],
      [
        29,
        34
      ],
      [
        14,
        32
      ],
      [
        10,
        17
      ],
      [
        22,
        31
      ],
      [
        15,
        21
      ],
      [
        20,
        33
      ],
      [
        32,
        42
      ],
      [
        25,
        34
      ],
      [
        27,
        34
      ],
      [
        16,
        28
      ],
      [
        27,
        36
      ],
      [
        23,
        33
      ],
      [
        35,
        43
      ],
      [
        12,
        26
      ],
      [
        27,
        39
      ],
      [
        29,
        33
      ],
      [
        10,
        28
      ],
      [
        16,
        23
      ],
      [
        21,
        36
      ],
      [
        16,
        37
      ],
      [
        18,
        25
      ],
      [
        20,
        30
      ],
      [
        13,
        20
      ],
      [
        21,
        27
      ],
      [
        26,
        31
      ],
      [
        24,
        38
      ],
      [
        16,
        31
      ],
      [
        13,
        31
      ],
      [
        23,
        30
      ],
      [
        18,
        26
      ],
      [
        13,
        23
      ],
      [
        25,
        42
      ],
      [
        23,
        31
      ],
      [
        12,
        19
      ],
      [
        24,
        33
      ],
      [
        22,
        30
      ],
      [
        24,
        29
      ],
      [
        21,
        31
      ],
      [
        18,
        27
      ],
      [
        18,
        27
      ],
      [
        38,
        42
      ],
      [
        17,
        25
      ],
      [
        26,
        32
      ],
      [
        28,
        34
      ],
      [
        19,
        30
      ],
      [
        18,
        32
      ],
      [
        14,
        24
      ],
      [
        13,
        27
      ],
      [
        15,
        24
      ],
      [
        17,
        25
      ],
      [
        35,
        39
      ],
      [
        31,
        55
      ],
      [
        12,
        20
      ],
      [
        11,
        28
      ],
      [
        28,
        40
      ],
      [
        24,
        31
      ],
      [
        14,
        30
      ],
      [
        12,
        48
      ],
      [
        14,
        20
      ],
      [
        15,
        28
      ],
      [
        29,
        40
      ],
      [
        26,
        35
      ],
      [
        27,
        33
      ],
      [
        19,
        29
      ],
      [
        30,
        40
      ],
      [
        34,
        38
      ],
      [
        37,
        42
      ],
      [
        13,
        20
      ],
      [
        17,
        30
      ],
      [
        25,
        36
      ]
    ],
    "standard_median_crossing_or_horizon": 31.0,
    "standard_rejection_rate": 1.0
  },
  "scope": {
    "executed": "All released synthetic notebook protocols (Figures 1, 2, 3, 5, and 6), plus an increasing-horizon power check.",
    "not_executed": "ImageNet-C, because author-required precomputed entropy arrays are not released."
  },
  "source_commit": "a9feb795d9fa98cc1d0c075f8f08a5c510c7a844",
  "type1_sweep": [
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 10,
      "naive_fixed_reference_type1_rate": 0.88,
      "reported_calibration_size": 0
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 500,
      "naive_fixed_reference_type1_rate": 0.33,
      "reported_calibration_size": 500
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 1000,
      "naive_fixed_reference_type1_rate": 0.17,
      "reported_calibration_size": 1000
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 1500,
      "naive_fixed_reference_type1_rate": 0.15,
      "reported_calibration_size": 1500
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 2000,
      "naive_fixed_reference_type1_rate": 0.07,
      "reported_calibration_size": 2000
    },
    {
      "conditional_minus_nominal": -0.04,
      "conditional_type1_rate": 0.01,
      "effective_calibration_size": 2500,
      "naive_fixed_reference_type1_rate": 0.08,
      "reported_calibration_size": 2500
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 3000,
      "naive_fixed_reference_type1_rate": 0.03,
      "reported_calibration_size": 3000
    },
    {
      "conditional_minus_nominal": -0.04,
      "conditional_type1_rate": 0.01,
      "effective_calibration_size": 3500,
      "naive_fixed_reference_type1_rate": 0.05,
      "reported_calibration_size": 3500
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 4000,
      "naive_fixed_reference_type1_rate": 0.06,
      "reported_calibration_size": 4000
    },
    {
      "conditional_minus_nominal": -0.04,
      "conditional_type1_rate": 0.01,
      "effective_calibration_size": 4500,
      "naive_fixed_reference_type1_rate": 0.07,
      "reported_calibration_size": 4500
    },
    {
      "conditional_minus_nominal": -0.05,
      "conditional_type1_rate": 0.0,
      "effective_calibration_size": 5000,
      "naive_fixed_reference_type1_rate": 0.07,
      "reported_calibration_size": 5000
    }
  ]
}

````


````output
wrote outputs/full_synthetic_summary.json
{
  "ar1": {
    "conditional": 1.0,
    "conditional_median_crossing_or_horizon": 12.0,
    "pairwise_detection_rate": 0.94,
    "pairwise_median_crossing_or_horizon": 149.0,
    "standard": 1.0,
    "standard_median_crossing_or_horizon": 17.0
  },
  "contamination_control": {
    "conditional_late_mean_ecdf": 0.7434000000000001,
    "fixed_reference_retains_more_shift_evidence": true,
    "protocol": "fixed N(0,1) calibration; 300 null then 2000 N(1,1) stream points",
    "standard_late_mean_rank_pvalue": 0.5550927611665414
  },
  "mode": "full-released-synthetic-protocol",
  "primary_power": {
    "conditional_faster": true,
    "conditional_median_crossing_or_horizon": 21.0,
    "conditional_rejection_rate": 1.0,
    "standard_median_crossing_or_horizon": 31.0,
    "standard_rejection_rate": 1.0
  },
  "type1_rates": [
    {
      "calibration_size": 0,
      "conditional": 0.0,
      "naive": 0.88
    },
    {
      "calibration_size": 500,
      "conditional": 0.0,
      "naive": 0.33
    },
    {
      "calibration_size": 1000,
      "conditional": 0.0,
      "naive": 0.17
    },
    {
      "calibration_size": 1500,
      "conditional": 0.0,
      "naive": 0.15
    },
    {
      "calibration_size": 2000,
      "conditional": 0.0,
      "naive": 0.07
    },
    {
      "calibration_size": 2500,
      "conditional": 0.01,
      "naive": 0.08
    },
    {
      "calibration_size": 3000,
      "conditional": 0.0,
      "naive": 0.03
    },
    {
      "calibration_size": 3500,
      "conditional": 0.01,
      "naive": 0.05
    },
    {
      "calibration_size": 4000,
      "conditional": 0.0,
      "naive": 0.06
    },
    {
      "calibration_size": 4500,
      "conditional": 0.01,
      "naive": 0.07
    },
    {
      "calibration_size": 5000,
      "conditional": 0.0,
      "naive": 0.07
    }
  ]
}

````


---
<!-- trackio-cell
{"type": "code", "id": "cell_ca304421a59e", "created_at": "2026-07-17T12:22:30+00:00", "title": "Pinned-source equivalence tests", "command": ["python", "-m", "pytest", "repro/tests", "-q"], "exit_code": 0, "duration_s": 0.812}
-->
````bash
$ python -m pytest repro/tests -q
````

exit 0 · 0.8s


````output
.....                                                                    [100%]
5 passed in 0.60s

````
