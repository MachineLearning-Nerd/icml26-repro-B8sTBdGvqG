"""experiments.py
-----------------
Reconstruction runner for the Conditional CTM paper (synth_exps.ipynb).

Public API
----------
one_exp(...)                 - single trial; returns a raw-results dict
sweep_power_motivating(...)  - Fig 2 right  : results_power_motivating
sweep_type1_vs_holdout(...)  - Fig 2 left   : (cond_ctm_rates, naive_rates)
sweep_power_biases(...)      - Fig 3 left   : results_power_biases
sweep_delay_ratios(...)      - Fig 3 middle : results_delay (delay_ratio col)
sweep_drift_slope(...)       - Fig 3 right  : results_drift_slope
sweep_clipping(...) - Fig 5        : pairwise_delay/imm DataFrames
sweep_ar1(...)               - Fig 6        : ar1_df
"""

from __future__ import annotations

import numpy as np

from cond_ctm import CondCTM
from conformal_test import ConformalTest
from pairwise import PairwiseBettingContinuous, simulate_ARm_process

__all__ = [
    "one_exp",
    "sweep_power_motivating",
    "sweep_type1_vs_holdout",
    "sweep_power_biases",
    "sweep_delay_ratios",
    "sweep_drift_slope",
    "sweep_clipping",
    "sweep_ar1",
]

# ---------------------------------------------------------------------------
# Paper defaults (match paper Section 4 + Appendix B settings)
# ---------------------------------------------------------------------------
_ALPHA: float = 0.05
_CI_DELTA: float = 0.1   # DKW delta for CondCTM
_D: float = 0.5           # ONS domain half-width
_CLIP_C: float = 0.1      # eta clipping threshold
_SMOOTH: float = 1e-6     # smoothing parameter k


# ---------------------------------------------------------------------------
# Core single-trial runner
# ---------------------------------------------------------------------------

def one_exp(
    mean_cal: float,
    std_cal: float,
    cal_samples: int,
    test_samples: int,
    ci_delta: float = _CI_DELTA,
    warmup_samples: int = 0,
    mode: str = "bias",     # "bias" | "drift" | "ar1"
    single_bias: float = 0.0,
    drift_slope: float = 0.0,
    delay_start: int = 0,   # absolute index in test stream where bias starts
    clip_C: float = _CLIP_C,
    D: float = _D,
    smooth_param: float = _SMOOTH,
    test_alpha: float = _ALPHA,
    only_cond_ctm: bool = False,
    include_pairwise: bool = True,
    seed: int | None = None,
) -> dict:
    """Run one experiment trial.

    Returns a dict with keys:
      max_prod         - maximum running martingale value
      bets             - list of per-step bet values (length = test_samples - warmup_samples)
      martingale_cond_ctm  - list, cumprod of bets
      conformal_result - (first_idx, np.ndarray martingales), length cal+test; or None
      pairwise_result  - wealth_sequence list from PairwiseBettingContinuous, or None
    """
    # Seed the legacy global RNG so that simulate_ARm_process is reproducible.
    if seed is not None:
        np.random.seed(seed)

    # --- calibration set (always i.i.d. null) ---
    effective_cal = max(cal_samples, 1)
    cal_set = np.random.normal(mean_cal, std_cal, effective_cal)

    # --- test set ---
    if mode == "ar1":
        # AR(1): X_{t+1} = 0.7*X_t + epsilon, epsilon ~ N(mu=1, sigma=1)
        test_set = simulate_ARm_process(test_samples, a=0.7, sigma=1.0, mu=1.0, m=1)
    else:
        test_set = np.random.normal(mean_cal, std_cal, test_samples)
        if mode == "bias" and single_bias != 0.0:
            # apply shift after delay_start
            test_set[delay_start:] += single_bias
        elif mode == "drift" and drift_slope != 0.0:
            # linearly increasing drift: test_set[t] += drift_slope * t / test_samples
            ts = np.arange(test_samples, dtype=float)
            test_set += drift_slope * ts / test_samples

    # --- CondCTM ---
    cond_ctm = CondCTM(ci_delta, cal_set, C=clip_C, D=D, smooth_param=smooth_param)

    # warmup: update ONS without placing bets
    for t in range(warmup_samples):
        cond_ctm.optim.step(cond_ctm.cal_ecdf(test_set[t]))

    # test: accumulate bets
    for t in range(warmup_samples, test_samples):
        cond_ctm.step(test_set[t])

    bets = list(cond_ctm.bets)
    martingale_cond_ctm = list(np.cumprod(bets)) if bets else []
    max_prod = float(np.max(martingale_cond_ctm)) if martingale_cond_ctm else 1.0

    # --- Standard CTM ---
    if only_cond_ctm:
        conformal_result = None
        pairwise_result = None
    else:
        conformal = ConformalTest(alpha=test_alpha, D=D)
        conformal_result = conformal.test_exchangeability(
            np.concatenate((cal_set, test_set)),
            cal_set_size=effective_cal,
            warmup_samples=warmup_samples,
            C=clip_C,
        )

        if include_pairwise:
            pairwise = PairwiseBettingContinuous(alpha=test_alpha)
            pr = pairwise.test_exchangeability(test_set, return_details=True, cal_samples=0)
            pairwise_result = list(pr["wealth_sequence"])
        else:
            pairwise_result = None

    return {
        "max_prod": max_prod,
        "bets": bets,
        "martingale_cond_ctm": martingale_cond_ctm,
        "conformal_result": conformal_result,
        "pairwise_result": pairwise_result,
    }


# ---------------------------------------------------------------------------
# Seed helper
# ---------------------------------------------------------------------------

def _trial_seed(base_seed: int, trial: int, offset: int = 0) -> int:
    """Unique seed per (base_seed, trial, offset) triple."""
    return (base_seed * 100_003 + offset * 997 + trial) & 0xFFFF_FFFF


# ---------------------------------------------------------------------------
# Figure 2 right – power comparison (motivating)
# ---------------------------------------------------------------------------

def sweep_power_motivating(
    n_exp: int = 100,
    cal_samples: int = 2000,
    test_samples: int = 1000,
    shift_mean: float = 1.0,
    base_seed: int = 0,
) -> list[dict]:
    """Immediate shift N(0,1) → N(shift_mean,1).  Keys: cal_samples, bets, conformal_result."""
    results = []
    for i in range(n_exp):
        r = one_exp(
            mean_cal=0.0, std_cal=1.0,
            cal_samples=cal_samples,
            test_samples=test_samples,
            ci_delta=_CI_DELTA,
            warmup_samples=0,
            mode="bias",
            single_bias=shift_mean,
            delay_start=0,
            clip_C=_CLIP_C,
            include_pairwise=False,
            seed=_trial_seed(base_seed, i),
        )
        results.append({
            "cal_samples": cal_samples,
            "bets": r["bets"],
            "conformal_result": r["conformal_result"],
        })
    return results


# ---------------------------------------------------------------------------
# Figure 2 left – Type-I error rate vs holdout set size
# ---------------------------------------------------------------------------

def sweep_type1_vs_holdout(
    n_exp: int = 100,
    cal_sizes: list[int] | None = None,
    test_samples: int = 20_000,
    base_seed: int = 0,
) -> tuple[list[float], list[float]]:
    """Null hypothesis holds (N(0,1) → N(0,1)).

    Returns (cond_ctm_rates, naive_rates):
      cond_ctm  – CondCTM with DKW CI (ci_delta=0.1)
      naive – CondCTM without CI (ci_delta=1)
    """
    if cal_sizes is None:
        cal_sizes = list(range(0, 5001, 500))

    threshold = 1.0 / _ALPHA
    cond_ctm_rates, naive_rates = [], []

    for cal_n in cal_sizes:
        effective_cal = max(cal_n, 10)   # avoid degenerate empty ECDF
        cond_ctm_rej = 0
        naive_rej = 0
        for i in range(n_exp):
            s = _trial_seed(base_seed, i, offset=cal_n)

            r_cond_ctm = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=effective_cal,
                test_samples=test_samples,
                ci_delta=_CI_DELTA,
                warmup_samples=0,
                mode="bias", single_bias=0.0,
                clip_C=_CLIP_C,
                only_cond_ctm=True,
                seed=s,
            )
            if r_cond_ctm["max_prod"] > threshold:
                cond_ctm_rej += 1

            r_naive = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=effective_cal,
                test_samples=test_samples,
                ci_delta=1.0,          # no CI correction
                warmup_samples=0,
                mode="bias", single_bias=0.0,
                clip_C=_CLIP_C,
                only_cond_ctm=True,
                seed=s,
            )
            if r_naive["max_prod"] > threshold:
                naive_rej += 1

        cond_ctm_rates.append(cond_ctm_rej / n_exp)
        naive_rates.append(naive_rej / n_exp)

    return cond_ctm_rates, naive_rates


# ---------------------------------------------------------------------------
# Figure 3 left – power vs bias magnitude (immediate shift)
# ---------------------------------------------------------------------------

def sweep_power_biases(
    n_exp: int = 100,
    biases: list[float] | None = None,
    cal_samples: int = 1000,
    test_samples: int = 1000,
    base_seed: int = 0,
) -> list[dict]:
    """Keys: single_bias, martingale_cond_ctm, conformal_result."""
    if biases is None:
        biases = [1.0, 1.5, 2.0]

    results = []
    for bias in biases:
        for i in range(n_exp):
            r = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=cal_samples,
                test_samples=test_samples,
                ci_delta=_CI_DELTA,
                warmup_samples=0,
                mode="bias",
                single_bias=bias,
                delay_start=0,
                clip_C=_CLIP_C,
                include_pairwise=False,
                seed=_trial_seed(base_seed, i, offset=int(bias * 100)),
            )
            results.append({
                "single_bias": bias,
                "martingale_cond_ctm": r["martingale_cond_ctm"],
                "conformal_result": r["conformal_result"],
            })
    return results


# ---------------------------------------------------------------------------
# Figure 3 middle – power vs delay (delayed change-point)
# ---------------------------------------------------------------------------

def sweep_delay_ratios(
    n_exp: int = 100,
    delay_ratios: list[float] | None = None,
    cal_samples: int = 1000,
    shift_mean: float = 2.0,
    warmup_samples: int = 100,
    base_seed: int = 0,
) -> list[dict]:
    """Keys: delay_ratio, martingale_cond_ctm, conformal_result.

    delay_ratio = delay_steps / cal_samples, so the plotting cell's
    ``delay_df["delay_steps"] = (delay_df["delay_ratio"] * cal_size).round()``
    recovers the correct absolute delay.

    test_samples is chosen to cover max(delay_steps) + 500 samples.
    """
    if delay_ratios is None:
        delay_ratios = [0.2, 0.6, 4.0]

    delay_steps_list = [round(r * cal_samples) for r in delay_ratios]
    test_samples = max(delay_steps_list) + 500

    results = []
    for delay_ratio, delay_steps in zip(delay_ratios, delay_steps_list):
        for i in range(n_exp):
            r = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=cal_samples,
                test_samples=test_samples,
                ci_delta=_CI_DELTA,
                warmup_samples=warmup_samples,
                mode="bias",
                single_bias=shift_mean,
                delay_start=delay_steps,
                clip_C=_CLIP_C,
                include_pairwise=False,
                seed=_trial_seed(base_seed, i, offset=delay_steps),
            )
            results.append({
                "delay_ratio": delay_ratio,
                "martingale_cond_ctm": r["martingale_cond_ctm"],
                "conformal_result": r["conformal_result"],
            })
    return results


# ---------------------------------------------------------------------------
# Figure 3 right – gradual drift
# ---------------------------------------------------------------------------

def sweep_drift_slope(
    n_exp: int = 100,
    drift_slopes: list[float] | None = None,
    cal_samples: int = 2000,
    test_samples: int = 100,
    base_seed: int = 0,
) -> list[dict]:
    """Keys: drift_slope, cal_samples, bets, conformal_result.

    Drift: test_set[t] += drift_slope * t / test_samples  (linearly increasing).
    """
    if drift_slopes is None:
        drift_slopes = [1.5, 3.0, 5.0]

    results = []
    for slope in drift_slopes:
        for i in range(n_exp):
            r = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=cal_samples,
                test_samples=test_samples,
                ci_delta=_CI_DELTA,
                warmup_samples=0,
                mode="drift",
                drift_slope=slope,
                clip_C=_CLIP_C,
                include_pairwise=False,
                seed=_trial_seed(base_seed, i, offset=int(slope * 10)),
            )
            results.append({
                "drift_slope": slope,
                "cal_samples": cal_samples,
                "bets": r["bets"],
                "conformal_result": r["conformal_result"],
            })
    return results


# ---------------------------------------------------------------------------
# Figure 5 – clipping ablation (CondCTM only, vary clip_C)
# ---------------------------------------------------------------------------

def sweep_clipping(
    n_exp: int = 100,
    clipping_params: list[float] | None = None,
    cal_samples: int = 2000,
    test_samples: int = 1000,
    delay_start: int = 0,
    base_seed: int = 0,
) -> list[dict]:
    """Keys: clipping_param, martingale_cond_ctm, conformal_result.

    Pass delay_start=800 for the delayed scenario, 0 for the immediate one.
    Note: conformal_result column is present for completeness; build_power_df
    only uses martingale_cond_ctm.
    """
    if clipping_params is None:
        clipping_params = [0.0, 0.05, 0.1, 0.2]

    results = []
    for c in clipping_params:
        for i in range(n_exp):
            r = one_exp(
                mean_cal=0.0, std_cal=1.0,
                cal_samples=cal_samples,
                test_samples=test_samples,
                ci_delta=_CI_DELTA,
                warmup_samples=0,
                mode="bias",
                single_bias=1.0,
                delay_start=delay_start,
                clip_C=c,
                only_cond_ctm=True,
                seed=_trial_seed(base_seed, i, offset=int(c * 1000)),
            )
            results.append({
                "clipping_param": c,
                "martingale_cond_ctm": r["martingale_cond_ctm"],
                "conformal_result": r["conformal_result"],
            })
    return results


# ---------------------------------------------------------------------------
# Figure 6 – AR(1) pairwise comparison
# ---------------------------------------------------------------------------

def sweep_ar1(
    n_exp: int = 100,
    cal_samples: int = 1000,
    test_samples: int = 2000,
    base_seed: int = 0,
) -> list[dict]:
    """Keys: cal_samples, martingale_cond_ctm, conformal_result, pairwise_result."""
    results = []
    for i in range(n_exp):
        r = one_exp(
            mean_cal=0.0, std_cal=1.0,
            cal_samples=cal_samples,
            test_samples=test_samples,
            ci_delta=_CI_DELTA,
            warmup_samples=0,
            mode="ar1",
            clip_C=_CLIP_C,
            include_pairwise=True,
            seed=_trial_seed(base_seed, i),
        )
        results.append({
            "cal_samples": cal_samples,
            "martingale_cond_ctm": r["martingale_cond_ctm"],
            "conformal_result": r["conformal_result"],
            "pairwise_result": r["pairwise_result"],
        })
    return results
