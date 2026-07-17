# Conditional Conformal Test Martingales — reproduction

This repository reproduces the two live Judge claims for **Testing For
Distribution Shifts with Conditional Conformal Test Martingales** (OpenReview
`B8sTBdGvqG`, arXiv `2602.13848`).  It pins the author implementation at
`shaersh/cctm@a9feb795d9fa98cc1d0c075f8f08a5c510c7a844` in `upstream/`.

The reproduction targets the released full synthetic protocol: the normal-null
and mean-shift streams, 100 independent repetitions, a 2,000-point calibration
set for the primary power experiment, and the paper's 20,000-step type-I sweep.
It uses a source-equivalent but asymptotically faster rank/ECDF evaluator so the
full CPU protocol is practical locally; unit tests compare its transitions with
the pinned implementation on identical streams.

## Live claims

1. Conditional CTM detects shifts faster than standard CTM because its reference
   set remains fixed rather than becoming contaminated by post-shift samples.
2. Conditional CTM gives anytime-valid type-I control and empirical power/delay
   behavior consistent with the paper's guarantee.

The paper also reports ImageNet-C results, but its repository requires private
precomputed entropy arrays and supplies neither the arrays nor download
instructions.  Those results will not be represented as reproduced unless the
authors' exact arrays become available.

## Status

See [STATUS.md](STATUS.md) and [the primary-source audit](docs/PRIMARY_SOURCE_AUDIT.md).

## Full synthetic result

The complete released synthetic notebook protocol was run with 100 repetitions
per source configuration (Figures 1, 2, 3, 5, and 6).  The saved artifact and
an implementation-independent re-aggregation are in
[`outputs/full_synthetic_summary.json`](outputs/full_synthetic_summary.json) and
[`outputs/independent_verification.json`](outputs/independent_verification.json).

- C1: in the primary `N(0,1) -> N(1,1)` setting, both methods detected all
  100 shifts, while conditional CTM's median crossing was 21 observations
  versus 31 for the growing-reference CTM.  Every bias, delayed-shift, and
  gradual-drift source sweep also had a lower conditional median delay.  The
  fixed-reference mechanism control retained a late-stream mean ECDF value of
  0.7434 versus 0.5551 for the growing-reference p-values.
- C2: conditional CTM's finite-sample false-positive rate was 0–1% across all
  11 released null configurations (nominal level 5%), whereas the deliberately
  uncorrected fixed-reference control reached 88% with no calibration data.
  Conditional CTM detected every mean-shift stream in each 100-run increasing-
  horizon check.  These numerical checks support the empirical behavior; they
  do not replace the paper's asymptotic proof.

Run the full reproduction from this directory with:

```bash
source .venv/bin/activate
python repro/run_full_synthetic.py --output outputs/full_synthetic_summary.json
python repro/verify_full_synthetic.py --input outputs/full_synthetic_summary.json --output outputs/independent_verification.json
```
