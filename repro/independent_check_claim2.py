"""Independent reconstruction of Claim 2 evidence without author imports."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


def close(left: float, right: float, tolerance: float = 1e-11) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads((args.artifact_dir / "raw_results.json").read_text())
    with (args.artifact_dir / "trajectory.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))

    parameters = raw["parameters"]
    n = int(parameters["reference_size"])
    delta = float(parameters["delta"])
    epsilon = math.sqrt(math.log(2.0 / delta) / (2.0 * n))
    k = float(parameters["equation8_k"])
    eta_fixed = float(parameters["equation8_eta"])
    threshold = float(parameters["threshold"])
    scale = 1.0 / (0.5 + math.sqrt(1.0 + k * k) * epsilon)
    expected_exact_bet = 1.0 + scale * (
        eta_fixed * 0.5 - math.sqrt(eta_fixed * eta_fixed + k * k) * epsilon
    )

    exact_wealth = 1.0
    released_wealth = 1.0
    eta = 0.0
    curvature = 1.0
    exact_crossing = -1
    released_crossing = -1
    transitions_match = True

    for row in rows:
        time = int(row["time"])
        u = float(row["empirical_cdf"])
        transitions_match &= (
            float(row["x_t"]) == 0.0
            and float(row["true_cdf"]) == 1.0
            and u == 1.0
            and close(float(row["equation8_bet"]), expected_exact_bet)
            and close(float(row["eta_before"]), eta)
        )

        eta_used = 0.0 if abs(eta) < 0.1 else eta
        denominator = 0.5 + (1.0 + k) * epsilon
        root = math.sqrt(eta_used * eta_used + k * k)
        released_bet = 1.0 + (
            eta_used * (u - 0.5) - root * epsilon
        ) / denominator
        released_wealth *= released_bet
        exact_wealth *= expected_exact_bet

        transitions_match &= (
            close(float(row["eta_used"]), eta_used)
            and close(float(row["released_bet"]), released_bet)
            and close(float(row["released_wealth"]), released_wealth)
            and close(float(row["equation8_wealth"]), exact_wealth)
        )

        if exact_crossing < 0 and exact_wealth >= threshold:
            exact_crossing = time
        if released_crossing < 0 and released_wealth >= threshold:
            released_crossing = time

        root_for_gradient = math.sqrt(eta * eta + k * k)
        v_dot_eta = (
            eta * (u - 0.5) - root_for_gradient * epsilon
        ) / denominator
        derivative = (
            u - 0.5 - eta * epsilon / root_for_gradient
        ) / denominator
        z = derivative / (1.0 + v_dot_eta)
        curvature += z * z
        eta = eta + (2.0 / (2.0 - math.log(3.0))) * z / curvature
        eta = max(-0.5, min(0.5, eta))
        transitions_match &= close(float(row["eta_after"]), eta)

    checks = {
        "trajectory_has_declared_horizon": len(rows)
        == int(parameters["horizon"]),
        "dkw_recomputed": close(epsilon, float(parameters["dkw_epsilon"])),
        "point_mass_ecdf_equals_true_cdf": all(
            float(row["empirical_cdf"]) == float(row["true_cdf"]) == 1.0
            for row in rows
        ),
        "all_transitions_reconstructed": transitions_match,
        "equation8_crossing_reconstructed": exact_crossing
        == raw["equation8"]["first_crossing"],
        "released_crossing_reconstructed": released_crossing
        == raw["released_algorithm"]["first_crossing"],
        "finite_witness_contradicts_inner_bound": 1.0
        > float(parameters["alpha"]),
        "deterministic_reference_contradicts_outer_bound": 0.0
        < 1.0 - delta,
    }
    passed = all(checks.values())
    result = {
        "claim_id": 2,
        "independent": True,
        "imports_released_code": False,
        "checks": checks,
        "reconstructed": {
            "dkw_epsilon": epsilon,
            "equation8_first_crossing": exact_crossing,
            "released_first_crossing": released_crossing,
            "equation8_final_wealth": exact_wealth,
            "released_final_wealth": released_wealth,
        },
        "passed": passed,
        "verdict": "FALSIFIED" if passed else "BLOCKED",
    }
    output = args.artifact_dir / "independent_checker_output.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM2_INDEPENDENT_OUTPUT=" + json.dumps(result, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
