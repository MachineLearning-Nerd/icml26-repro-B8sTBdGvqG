# Claim 2 — FALSIFIED: Theorem 3.1 finite-sample type-I statement

Verdict: `FALSIFIED`.

Exact claim tested: Theorem 3.1 states anytime-valid type-I error control for any null distribution `P`, any `alpha`, and confidence bounds satisfying Equation 6, with probability at least `1-delta` over the reference set.

The witness uses a Dirac point-mass null distribution at 0. The reference set and stream are iid from the same null, the empirical CDF equals the true CDF exactly, and the DKW/Equation 6 event holds with probability 1.

Key numbers from the verifier:

- `P`: Dirac point mass at 0, inside the paper's stated `any P` domain.
- Reference size: 2000; horizon container: 64; `alpha=0.05`; `delta=0.1`.
- DKW epsilon: `0.027366641525559867`; supremum ECDF error: `0.0`.
- Equation 8 first crossing: `9`; released algorithm first crossing: `10`.
- Actual inner false-rejection probability: `1.0`; theorem requires at most `0.05`.
- Actual outer good-reference probability: `0.0`; theorem requires at least `0.9`.

Raw evidence:

- [claim contract](../../evidence/claim_2/claim_contract.json)
- [raw results](../../evidence/claim_2/prior_run_raw_results.json)
- [trajectory CSV](../../evidence/claim_2/prior_run_trajectory.csv)
- [verifier output](../../evidence/claim_2/prior_run_verifier_output.json)
- [independent checker output](../../evidence/claim_2/prior_run_independent_checker_output.json)
- [negative controls](../../evidence/claim_2/prior_run_negative_controls.json)
- [method](../../evidence/claim_2/method.md), [source audit](../../evidence/claim_2/source_audit.md), [limitations](../../evidence/claim_2/limitations.md)

Visible code:

- [counterexample runner](../../code/repro/run_claim2_counterexample.py)
- [claim verifier](../../code/repro/verify_claim2_counterexample.py)
- [independent checker](../../code/repro/independent_check_claim2.py)
- [frozen regression checker](../../code/repro/verify_frozen_claim2.py)

Negative controls: randomized PIT at the atom reduces the rejection rate to `0.00390625`, and the reverse-direction bet does not cross. These controls show the falsification is tied to ordinary PIT/tie handling under a discrete null, not to a generic checker bug.

Independent checker: passed = `true`, imports released code = `false`.
