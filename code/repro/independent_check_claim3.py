"""Independent stdlib checker for the Claim 3 symbolic certificate."""

from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    certificate = json.loads(
        (args.artifact_dir / "proof_certificate.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "negative_controls.json").read_text()
    )

    # Exhaustive rational audit over both feasible-benchmark branches.
    grid_checks = 0
    benchmark_bound_holds = True
    variance_coupling_holds = True
    for c_index in range(1, 9):
        c = Fraction(c_index, 8)
        for d_index in range(1, 9):
            d = Fraction(d_index, 16) / c
            if c * d > 1:
                continue
            for m_index in range(1, 17):
                m2 = Fraction(m_index, 16) / (c * c)
                if m2 < d * d or m2 > 1 / (c * c):
                    continue
                q = min(d / (2 * m2), c / 2)
                lower = q * d - q * q * m2
                target = c * c * d * d / 4
                variance_upper = q * q * m2
                benchmark_bound_holds &= lower >= target
                variance_coupling_holds &= variance_upper <= lower
                grid_checks += 1

    # Direct numerical audit of the explicit burn-in inequality, deliberately
    # using values unrelated to any experiment or formula-derived sample size.
    burn_in_holds = True
    burn_in_checks = 0
    for alpha in (0.5, 0.1, 0.05, 0.01, 1e-4):
        for mu in (0.4, 0.2, 0.05, 0.01, 1e-4):
            L = math.log(1.0 / alpha) + math.log(64.0 / mu) + 1.0
            t0 = math.ceil(64.0 * L / mu)
            lhs = 2.0 * math.log(1.0 + 4.0 * t0) + 0.5 + math.log(
                1.0 / alpha
            )
            rhs = t0 * mu / 2.0
            burn_in_holds &= lhs <= rhs
            burn_in_checks += 1

    checks = {
        "certificate_declares_all_obligations": len(certificate["obligations"])
        == 11,
        "certificate_obligations_pass": all(
            item["passed"] for item in certificate["obligations"]
        ),
        "rational_case_split_nonvacuous": grid_checks >= 100,
        "rational_benchmark_bound_holds": benchmark_bound_holds,
        "rational_variance_coupling_holds": variance_coupling_holds,
        "burn_in_grid_nonvacuous": burn_in_checks == 25,
        "explicit_burn_in_holds": burn_in_holds,
        "unconstrained_error_detected": controls[
            "unconstrained_maximizer_error"
        ]["error_detected"],
        "tail_rate_error_detected": controls[
            "geometric_rate_substitution_error"
        ]["error_detected"],
        "final_verdict_verified": certificate["verdict"] == "VERIFIED",
    }
    passed = all(checks.values())
    output = {
        "claim_id": 3,
        "independent": True,
        "imports_sympy_or_author_code": False,
        "rational_grid_checks": grid_checks,
        "burn_in_checks": burn_in_checks,
        "checks": checks,
        "passed": passed,
        "verdict": "VERIFIED" if passed else "BLOCKED",
    }
    (args.artifact_dir / "independent_checker_output.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM3_INDEPENDENT_OUTPUT=" + json.dumps(output, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
