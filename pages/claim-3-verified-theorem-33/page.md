# Claim 3 — VERIFIED: Theorem 3.3 asymptotic power and stopping-time order

Verdict: `VERIFIED`.

Exact claim tested: conditional on fixed `D0`, for iid `X_t ~ Q != P`, sufficiently small positive smoothing `k`, and positive effective signal strength `Delta_k`, Algorithm 1 has asymptotic power one and expected stopping time of order `O(Delta_0^-2 log(1/(alpha Delta_0)) + Delta_0^-2)` as `k -> 0`.

This route is proof-level, not a finite simulation. The verifier checks a corrected symbolic derivation against the paper's theorem statement and assumptions.

Key verifier facts:

- Proof obligations passed: 11/11.
- Independent checker passed: `true`.
- Rational benchmark/case-split checks: `952`.
- Burn-in checks: `25`.
- Negative controls detect two proof-level errors: an unconstrained-maximizer mistake and a tail-rate substitution mistake.

Raw evidence:

- [claim contract](../../evidence/claim_3/claim_contract.json)
- [proof certificate](../../evidence/claim_3/proof_certificate.json)
- [verifier output](../../evidence/claim_3/verifier_output.json)
- [independent checker output](../../evidence/claim_3/independent_checker_output.json)
- [negative controls](../../evidence/claim_3/negative_controls.json)
- [method](../../evidence/claim_3/method.md), [source audit](../../evidence/claim_3/source_audit.md), [limitations](../../evidence/claim_3/limitations.md)

Visible code:

- [proof verifier](../../code/repro/verify_claim3_proof.py)
- [contract verifier](../../code/repro/verify_claim3_contract.py)
- [independent checker](../../code/repro/independent_check_claim3.py)
- [frozen regression checker](../../code/repro/verify_frozen_claim3.py)

Limitations: this is not a Lean/Coq certificate. It is a reproducible symbolic certificate plus an implementation-independent checker, so confidence is `MEDIUM` rather than `HIGH`.
