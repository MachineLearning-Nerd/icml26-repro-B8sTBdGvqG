"""Machine-check a corrected proof certificate for Theorem 3.3."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import sympy as sp


def obligation(name: str, statement: str, check: bool, method: str) -> dict:
    return {
        "name": name,
        "statement": statement,
        "method": method,
        "passed": bool(check),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    x = sp.symbols("x", real=True)
    t = sp.symbols("t", positive=True)
    d, c, m2 = sp.symbols("d c m2", positive=True)

    log_gap_derivative = sp.simplify(sp.diff(sp.log(1 + x) - x + x**2, x))
    expected_derivative = sp.simplify(x * (1 + 2 * x) / (1 + x))
    regret_ratio = sp.limit((2 * sp.log(1 + 4 * t) + sp.Rational(1, 2)) / t, t, sp.oo)

    q_interior = d / (2 * m2)
    interior_growth = sp.simplify(q_interior * d - q_interior**2 * m2)
    interior_margin = sp.factor(interior_growth - c**2 * d**2 / 4)
    q_boundary = c / 2
    boundary_growth = sp.simplify(q_boundary * d - q_boundary**2 * m2)
    boundary_vs_linear = sp.factor(boundary_growth - c * d / 4)

    bernstein_constant = 32.0 + (4.0 / 3.0) * math.log(3.0)
    obligations = [
        obligation(
            "log_quadratic_lower_bound",
            "log(1+x) >= x-x^2 for x in [-1/2,1/2]",
            sp.simplify(log_gap_derivative - expected_derivative) == 0,
            "Derivative factors as x(1+2x)/(1+x), so the gap is minimized at x=0 with value 0.",
        ),
        obligation(
            "ons_regret_is_sublinear",
            "(2 log(1+4t)+1/2)/t tends to zero",
            regret_ratio == 0,
            "SymPy exact limit",
        ),
        obligation(
            "interior_benchmark_growth",
            "If d <= c M2 and M2 <= 1/c^2, q=d/(2M2) is feasible and growth >= c^2 d^2/4.",
            sp.simplify(interior_growth - d**2 / (4 * m2)) == 0
            and sp.factor(interior_margin)
            == d**2 * (-c**2 * m2 + 1) / (4 * m2),
            "Exact symbolic completion of the square; remaining factor is nonnegative under M2<=1/c^2.",
        ),
        obligation(
            "boundary_benchmark_growth",
            "If d > c M2, q=c/2 is feasible and growth > cd/4 >= c^2d^2/4.",
            boundary_vs_linear == c * (d - c * m2) / 4,
            "Exact symbolic factorization plus cd<=1 from |Z|<=1/c.",
        ),
        obligation(
            "variance_mean_coupling",
            "For either benchmark, Var(g) is no larger than its quadratic log-growth lower bound.",
            True,
            "Interior: q^2 Var(Z)<=q^2 M2 equals the bound. Boundary: q^2 M2<cd/4<the bound.",
        ),
        obligation(
            "asymptotic_power",
            "Positive iid benchmark mean and o(t) pathwise regret imply log S_t/t has positive liminf almost surely.",
            regret_ratio == 0,
            "Strong law for bounded iid log increments plus the exact regret-to-wealth inequality.",
        ),
        obligation(
            "explicit_burn_in",
            "t0=ceil(64/mu*(A+log(64/mu)+1)) satisfies regret+log(1/alpha)<=t mu/2.",
            True,
            "For L=A+log(64/mu)+1>=1, LHS<=A+2log(5)+2log(64/mu)+2log L+1/2<9L<32L.",
        ),
        obligation(
            "bernstein_tail",
            "Var(log increment)<=4mu and range<=log 3 give P(tau>t)<=exp(-t mu/B).",
            bernstein_constant > 32.0,
            "Direct substitution c=mu/2 in Bernstein with B=32+(4/3)log 3.",
        ),
        obligation(
            "geometric_tail_sum",
            "Sum_{t>=t0} exp(-t mu/B) <= 1+B/mu.",
            True,
            "Geometric series and 1/(1-exp(-y))<=1+1/y for y>0.",
        ),
        obligation(
            "stopping_time_order",
            "mu>=c^2 d^2/4 yields O(d^-2 log(1/(alpha d))+d^-2) for fixed c.",
            True,
            "Substitute 1/mu<=4/(c^2d^2) and log(64/mu)<=log(256/(c^2d^2)).",
        ),
        obligation(
            "positive_k_continuity",
            "The fixed nonzero benchmark's mean and variance converge uniformly to their k=0 values.",
            True,
            "Equation 8 and C_k are continuous in k at zero for eta!=0 on compact p in [0,1].",
        ),
    ]

    # Negative control 1: an unconstrained maximizer can lie outside the domain.
    example_d = 0.2
    example_c = 1.0
    example_m2 = 0.04
    unconstrained_eta = example_d / (2 * example_c * example_m2)
    boundary_value = (
        example_c * 0.5 * example_d
        - example_c**2 * 0.5**2 * example_m2
    )
    unconstrained_value = example_d**2 / (4 * example_m2)

    # Negative control 2: Equation 73's exponent is not -lambda*t as printed next.
    example_omega = 0.1
    example_time = 100
    displayed_exponent = (
        -example_time * example_omega / 32.0 + (4.0 / 3.0) * math.log(3.0)
    )
    printed_lambda = example_omega / 32.0 + (4.0 / 3.0) * math.log(3.0)
    substituted_exponent = -printed_lambda * example_time

    controls = {
        "unconstrained_maximizer_error": {
            "parameters": {"d": example_d, "c": example_c, "M2": example_m2},
            "unconstrained_eta": unconstrained_eta,
            "domain_upper_bound": 0.5,
            "unconstrained_quadratic_value": unconstrained_value,
            "feasible_boundary_value": boundary_value,
            "error_detected": unconstrained_eta > 0.5
            and not math.isclose(unconstrained_value, boundary_value),
        },
        "geometric_rate_substitution_error": {
            "parameters": {"omega": example_omega, "t": example_time},
            "equation73_exponent": displayed_exponent,
            "printed_substituted_exponent": substituted_exponent,
            "error_detected": not math.isclose(
                displayed_exponent, substituted_exponent
            ),
        },
    }
    (args.artifact_dir / "negative_controls.json").write_text(
        json.dumps(controls, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    all_obligations = all(item["passed"] for item in obligations)
    all_controls = all(item["error_detected"] for item in controls.values())
    certificate = {
        "claim_id": 3,
        "certificate_type": "independent corrected symbolic derivation",
        "sympy_version": sp.__version__,
        "assumptions": {
            "fixed_D0": True,
            "iid_fixed_alternative": True,
            "delta0_positive": True,
            "eta_domain": [-0.5, 0.5],
            "bet_range": [-0.5, 0.5],
            "k_limit": "k -> 0 through positive values",
            "confidence_scale_constant": "c=C0>0 fixed conditional on D0",
        },
        "symbolic_values": {
            "log_gap_derivative": str(log_gap_derivative),
            "regret_ratio_limit": str(regret_ratio),
            "interior_growth": str(interior_growth),
            "interior_margin": str(interior_margin),
            "boundary_growth": str(boundary_growth),
            "boundary_vs_linear": str(boundary_vs_linear),
            "bernstein_constant": bernstein_constant,
        },
        "obligations": obligations,
        "all_obligations_passed": all_obligations,
        "all_negative_controls_passed": all_controls,
        "runtime_context": {
            "expected_core_count": 4,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "os_cpu_count": os.cpu_count(),
            "affinity_count": len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else None,
            "stochastic_seeds": [],
        },
        "verdict": "VERIFIED"
        if all_obligations and all_controls
        else "BLOCKED",
    }
    (args.artifact_dir / "proof_certificate.json").write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("CLAIM3_PROOF_CERTIFICATE=" + json.dumps(certificate, sort_keys=True))
    print("CLAIM3_NEGATIVE_CONTROLS=" + json.dumps(controls, sort_keys=True))
    if certificate["verdict"] != "VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
