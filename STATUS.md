# Status — Conditional Conformal Test Martingales

Updated for the repository cleanup on 2026-08-15.

## Scope

This is a scoped independent audit of arXiv `2602.13848` v2 and the pinned `shaersh/cctm` source commit. It is not a claim of complete paper reproduction, a new official evaluator score, or author endorsement.

## Claim matrix

| Claim | State | Evidence boundary |
|---|---|---|
| C1: faster shift detection | `VERIFIED_SCOPED` | The full released synthetic suites and contamination mechanism check pass; ImageNet-C is excluded. |
| C2: Theorem 3.1 anytime validity | `FALSIFIED_AS_WRITTEN` | The Dirac-null witness satisfies the theorem's printed any-distribution domain and is independently reconstructed. The finite Gaussian/null sweeps are retained as empirical context only. |
| C3: Theorem 3.3 power and delay order | `VERIFIED_PROOF_AUDIT` | A corrected proof certificate passes 11 obligations, 952 rational checks, 25 burn-in checks, and independent validation. This is not a proof-assistant formalization. |
| C4: DKW correction | `VERIFIED_SCOPED` | The full synthetic artifact and no-DKW negative control pass. |
| C5: synthetic power/delay | `VERIFIED_SCOPED` | All nine released bias/delay/drift settings and independent aggregation pass. |
| C6: ImageNet-C Figure 4 | `BLOCKED` | Sixteen required entropy inputs are absent; the plot can be digitized but not independently regenerated; reconstruction jobs stalled before inference. |

## Reproduction status

- Focused source-equivalence tests cover the conditional and growing-reference recurrences, DKW band, warm-up behavior, and the primary detection prefix.
- `evidence/synthetic/independent_verification.json` is the durable independent aggregation for C1/C4/C5.
- C2's independent checker does not import the released implementation.
- C3's independent checker does not import SymPy or author code.
- C6 has four separate routes, each fail-closed and non-claiming when required data are absent.
- No current author response, score increase, or endorsement is claimed.

## Historical publication context

The July 26, 2026 evaluator-visible package recorded a previous live score of `6/12` and a later `10/12` forecast. Those values are preserved as provenance only. The final GitHub repository is the auditable source of the scoped judgments above.

## Next evidence needed

Claim 6 can move from `BLOCKED` only after either the authors' raw entropy arrays or a faithful, full-scope ImageNet-C reconstruction becomes available: all 15 corruption types, severity 5, 37,500-example streams, 10 realizations, the specified reference sizes, independent re-aggregation, and negative controls must be present. A subset, proxy, digitized plot, or infrastructure failure is insufficient.

## Attribution and thanks

The maintained audit is attributed to `MachineLearning-Nerd`. Thank you to Shalev Shaer, Yarin Bar, Drew Prinster, and Yaniv Romano for releasing the paper and implementation that make this audit possible.
