# Primary-source audit

## Sources pinned

- Paper: arXiv `2602.13848`, *Testing For Distribution Shifts with Conditional
  Conformal Test Martingales*.
- Official repository: `shaersh/cctm`, commit
  `a9feb795d9fa98cc1d0c075f8f08a5c510c7a844`.

## Live Judge claims

1. Faster shift detection than standard conformal test martingales by avoiding
   test-time contamination.
2. Anytime-valid type-I control, asymptotic power one, and bounded expected
   detection delay.

## Exact released synthetic protocol

`upstream/experiments.py` and `upstream/synth_exps.ipynb` specify the primary
protocol used here:

- nominal test level `alpha=0.05`; DKW confidence parameter `delta=0.1`;
  ONS diameter `D=0.5`; clipping `C=0.1`; smoothing `k=1e-6`;
- primary immediate-shift comparison: 100 repetitions, calibration size 2,000,
  1,000 test observations, `N(0,1)` null to `N(1,1)` alternative;
- finite-reference validity sweep: 100 repetitions at each calibration size
  0,500,…,5,000 and a 20,000-observation null stream;
- supporting suites: bias levels 1/1.5/2, delayed shifts, gradual drift,
  clipping controls, and AR(1) controls.

The pinned baseline uses growing-reference randomized conformal p-values.  The
proposed method uses a fixed calibration ECDF and DKW band in the betting
function.  The independent runner preserves those recurrences exactly while
replacing repeated linear scans with `searchsorted`/Fenwick rank queries.

## Scope limitation

The official ImageNet-C runner requires `offline_imagenet/vitbase_timm` entropy
arrays.  The repository contains neither those arrays nor an acquisition script.
The full released synthetic suite is reproducible on this CPU host; the missing
ImageNet-C artifacts remain an explicit source-data limitation.

