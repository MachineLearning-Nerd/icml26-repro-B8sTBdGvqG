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

