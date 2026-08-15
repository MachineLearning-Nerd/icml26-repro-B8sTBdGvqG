# Conditional Conformal Test Martingales — audit entrypoint

This logbook preserves the original evaluator-visible reproduction package and the current independent audit of [arXiv 2602.13848](https://arxiv.org/abs/2602.13848).

## Current decision surface

| Claim | Verdict | Entry |
|---|---|---|
| C1 | `VERIFIED_SCOPED` | [Faster shift detection](#/claim-1-faster-shift-detection) |
| C2 | `FALSIFIED_AS_WRITTEN` | [Theorem 3.1 counterexample](#/claim-2-falsified-theorem-31) |
| C3 | `VERIFIED_PROOF_AUDIT` | [Theorem 3.3 proof audit](#/claim-3-verified-theorem-33) |
| C4/C5 | `VERIFIED_SCOPED` | [Current verification](#/current-verification-2026-07-26) and [negative controls](#/negative-controls) |
| C6 | `BLOCKED` | [ImageNet-C blocked record](#/claim-6-blocked-imagenet-c) |

The full claim production path is in [`CLAIM_EVIDENCE.md`](../CLAIM_EVIDENCE.md), the branch purpose map is in [`BRANCH_AUDIT.md`](../BRANCH_AUDIT.md), and pinned source details are in [`SOURCE_MANIFEST.md`](../SOURCE_MANIFEST.md).

## Paper

*Testing For Distribution Shifts with Conditional Conformal Test Martingales* by Shalev Shaer, Yarin Bar, Drew Prinster, and Yaniv Romano. See the [arXiv abstract](https://arxiv.org/abs/2602.13848) and [OpenReview record](https://openreview.net/forum?id=B8sTBdGvqG).

## Reproduction boundary

The synthetic protocol and theorem audits are reproducible from the committed artifacts. ImageNet-C remains blocked because the official entropy arrays are not released; digitized source plots and stalled infrastructure are not presented as benchmark results.
