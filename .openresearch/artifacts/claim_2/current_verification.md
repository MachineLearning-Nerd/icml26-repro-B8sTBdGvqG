# Current verification — Claim 2 / Theorem 3.1

**Verdict: FALSIFIED as written.** This page supersedes the earlier empirical
type-I sweep, which is retained only as a historical rejected baseline for this
theorem claim.

The theorem says its finite-sample anytime guarantee holds for any null
distribution. The point-mass null \(P=\delta_0\) is in that stated domain. Its
reference set and stream are iid from the same \(P\), and its ECDF equals the
true CDF exactly, so Equation 6 holds with zero error.

Nevertheless, ordinary non-randomized ECDF values are all 1. Equation 8 crosses
\(1/\alpha=20\) at step 9, and the released ONS implementation crosses at step
10. Since the reference and stream are deterministic under this \(P\), the
inner false-alarm probability is exactly 1 rather than at most 0.05, and the
outer good-reference probability is 0 rather than at least 0.9.

The proof's probability-integral-transform step is the source of the
contradiction: \(F(X)=1\), not Uniform(0,1), for the point mass. The paper did
not state a continuity assumption or use randomized tie handling.

## Direct evidence

- Claim contract: `claim_contract.json`
- Exact source and assumption audit: `source_audit.md`
- Method: `method.md`
- Raw result: `prior_run_raw_results.json`
- Raw controls: `prior_run_negative_controls.json`
- Fail-closed verifier: `prior_run_verifier_output.json`
- Independent checker: `prior_run_independent_checker_output.json`
- Command, Git SHA, CPU, and runtime: `prior_run_metadata.json`
- Executable sources:
  `repro/run_claim2_counterexample.py`,
  `repro/verify_claim2_counterexample.py`, and
  `repro/independent_check_claim2.py`

## Controls and limitations

Reversing the betting direction did not cross. Randomizing the PIT at the atom
rejected 1/256 streams (0.00390625), showing that the deterministic rejection
is caused by the unstated continuity/tie issue rather than a threshold bug.
This verdict does not adjudicate a repaired theorem restricted to continuous
nulls or using randomized PIT values.

## Historical rejected baseline

The earlier Gaussian type-I sweep remains useful empirical context, but it
cannot establish a universally quantified theorem and is not the current
verifier.
