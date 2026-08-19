# Scoped reproduction report

## Final verdict

`MIXED_RESULTS_SCOPED_AUDIT` — C1, C3, C4, and C5 are supported within their
declared evidence scopes; C2 is falsified as written by an assumption-matched
Dirac-null counterexample; and C6 is blocked because the required ImageNet-C
entropy arrays and raw tables are unavailable.

| Claim | Verdict | Evidence boundary |
| --- | --- | --- |
| C1 | `VERIFIED_SCOPED` | Released synthetic shift suites and fixed-reference mechanism control; ImageNet-C excluded. |
| C2 | `FALSIFIED_AS_WRITTEN` | The printed any-null-distribution theorem has a valid Dirac-null counterexample. |
| C3 | `VERIFIED_PROOF_AUDIT` | Corrected proof certificate with independent checks; not a proof-assistant formalization. |
| C4 | `VERIFIED_SCOPED` | Corrected DKW versus no-DKW synthetic control. |
| C5 | `VERIFIED_SCOPED` | Nine released synthetic settings and null controls with independent aggregation. |
| C6 | `BLOCKED` | Full ImageNet-C inputs and raw Figure 4 tables remain unavailable. |

## What is established

The claim ledger records each producer, source anchor, raw artifact, independent
checker, negative control, and limitation. The published branch set preserves
the synthetic baseline, theorem counterexample, proof correction, Claim 6
reconstruction attempts, and release surfaces as purpose-based branches.

## What is not established

Finite simulations do not prove universal or asymptotic theorems. Historical
judge scores and projections are provenance only. The repository does not claim
a complete ImageNet-C reproduction, a new evaluator score, or author
endorsement. `publication_allowed` is `false` for a paper-wide reproduction.
