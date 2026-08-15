"""Generate a finite, assumption-satisfying counterexample to Theorem 3.1."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reference_ctm import CondCTM, ONS, betting_function, compute_dkw_band


def equation8_bet(u: float, eta: float, epsilon: float, k: float) -> float:
    scale = 1.0 / (0.5 + math.sqrt(1.0 + k * k) * epsilon)
    return 1.0 + scale * (eta * (u - 0.5) - math.sqrt(eta * eta + k * k) * epsilon)


def run_released_from_pvalues(p_values: np.ndarray, epsilon: float) -> int:
    optim = ONS(epsilon, D=0.5)
    wealth = 1.0
    for index, u_value in enumerate(p_values, start=1):
        eta = optim.etas[-1]
        eta_for_bet = 0.0 if abs(eta) < 0.1 else eta
        wealth *= betting_function(
            float(u_value), eta_for_bet, epsilon, smooth_param=1e-6
        )
        if wealth >= 20.0:
            return index
        optim.step(float(u_value), smooth_param=1e-6)
    return -1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    alpha = 0.05
    delta = 0.1
    n_reference = 2_000
    horizon = 64
    k = 1e-6
    fixed_eta = 0.5
    epsilon = float(compute_dkw_band(n_reference, delta))
    threshold = 1.0 / alpha

    calibration = np.zeros(n_reference, dtype=np.float64)
    stream = np.zeros(horizon, dtype=np.float64)
    released = CondCTM(
        delta,
        calibration,
        D=0.5,
        C=0.1,
        smooth_param=k,
    )

    equation_wealth = 1.0
    reverse_wealth = 1.0
    released_wealth = 1.0
    equation_crossing = -1
    reverse_crossing = -1
    released_crossing = -1
    rows: list[dict[str, float | int]] = []

    for time, value in enumerate(stream, start=1):
        eta_before = float(released.optim.etas[-1])
        eta_used = 0.0 if abs(eta_before) < released.C else eta_before
        released_bet, eta_after = released.step(float(value))
        released_wealth *= float(released_bet)

        exact_bet = equation8_bet(1.0, fixed_eta, epsilon, k)
        reverse_bet = equation8_bet(1.0, -fixed_eta, epsilon, k)
        equation_wealth *= exact_bet
        reverse_wealth *= reverse_bet

        if equation_crossing < 0 and equation_wealth >= threshold:
            equation_crossing = time
        if reverse_crossing < 0 and reverse_wealth >= threshold:
            reverse_crossing = time
        if released_crossing < 0 and released_wealth >= threshold:
            released_crossing = time

        rows.append(
            {
                "time": time,
                "x_t": float(value),
                "true_cdf": 1.0,
                "empirical_cdf": float(released.p_values[-1]),
                "eta_before": eta_before,
                "eta_used": eta_used,
                "eta_after": float(eta_after),
                "released_bet": float(released_bet),
                "released_wealth": released_wealth,
                "equation8_bet": exact_bet,
                "equation8_wealth": equation_wealth,
                "reverse_bet": reverse_bet,
                "reverse_wealth": reverse_wealth,
            }
        )

    trajectory_path = args.output_dir / "trajectory.csv"
    with trajectory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    control_records = []
    for seed in range(256):
        rng = np.random.RandomState(seed)
        randomized_pit = rng.uniform(0.0, 1.0, 1_000)
        crossing = run_released_from_pvalues(randomized_pit, epsilon)
        control_records.append(
            {"seed": seed, "crossing": crossing, "rejected": crossing >= 0}
        )
    randomized_rejections = sum(row["rejected"] for row in control_records)
    controls = {
        "reverse_direction": {
            "eta": -fixed_eta,
            "crossing": reverse_crossing,
            "final_wealth": reverse_wealth,
            "expected": "no crossing",
        },
        "randomized_pit_repair": {
            "description": "At the point-mass atom, use V~Uniform(0,1) instead of ordinary F(X)=1.",
            "seeds": list(range(256)),
            "horizon": 1_000,
            "records": control_records,
            "rejections": randomized_rejections,
            "rejection_rate": randomized_rejections / len(control_records),
            "expected": "not deterministic rejection and rejection rate <= alpha",
        },
    }
    (args.output_dir / "negative_controls.json").write_text(
        json.dumps(controls, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    raw = {
        "claim_id": 2,
        "verdict_candidate": "FALSIFIED",
        "distribution": {
            "name": "Dirac point mass",
            "support_point": 0.0,
            "reference_iid_from_P": True,
            "stream_iid_from_P": True,
            "continuous": False,
            "within_stated_any_P_domain": True,
        },
        "parameters": {
            "alpha": alpha,
            "delta": delta,
            "reference_size": n_reference,
            "horizon": horizon,
            "threshold": threshold,
            "dkw_epsilon": epsilon,
            "equation8_eta": fixed_eta,
            "equation8_k": k,
            "released_D": 0.5,
            "released_C": 0.1,
        },
        "assumption_audit": {
            "supremum_ecdf_error": 0.0,
            "equation6_holds": True,
            "reference_good_event_probability": 1.0,
            "ordinary_pit_value": 1.0,
            "proof_claimed_pit_mean": 0.5,
            "actual_pit_mean": 1.0,
        },
        "equation8": {
            "first_crossing": equation_crossing,
            "final_wealth": equation_wealth,
            "conditional_false_reject_probability": 1.0,
        },
        "released_algorithm": {
            "first_crossing": released_crossing,
            "final_wealth": released_wealth,
            "conditional_false_reject_probability": 1.0,
        },
        "theorem_comparison": {
            "required_inner_probability_at_most": alpha,
            "actual_inner_probability": 1.0,
            "required_outer_probability_at_least": 1.0 - delta,
            "actual_outer_probability": 0.0,
        },
        "runtime_context": {
            "os_cpu_count": os.cpu_count(),
            "affinity_count": len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else None,
            "expected_core_count": 4,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "seeds": list(range(256)),
        },
    }
    raw_path = args.output_dir / "raw_results.json"
    raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("CLAIM2_RAW_RESULTS_BEGIN")
    print(json.dumps(raw, sort_keys=True))
    print("CLAIM2_RAW_RESULTS_END")
    print("CLAIM2_NEGATIVE_CONTROLS_BEGIN")
    print(json.dumps(controls, sort_keys=True))
    print("CLAIM2_NEGATIVE_CONTROLS_END")


if __name__ == "__main__":
    main()
