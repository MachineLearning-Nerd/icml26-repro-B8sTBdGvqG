# Status — Conditional Conformal Test Martingales

## Current step

Full source-scale synthetic reproduction and independent re-aggregation passed.

## Claims and evidence plan

| Claim | Required full-scope evidence | State |
|---|---|---|
| C1 | 100-repetition N(0,1)→N(1,1) power/detection-delay comparison, every released bias/delay/drift sweep, clipping/AR(1) support, and fixed-vs-growing-reference mechanism check | passed: primary median 21 vs 31; all 9 source bias/delay/drift settings faster; independent artifact re-aggregation passed |
| C2 | 100-repetition null sweep over the released 11-size calibration grid and horizon, plus increasing-horizon power/delay checks and independent transition tests | passed empirically: 0–1% conditional Type-I across all 11 settings; no-DKW negative control reaches 88%; every horizon check detects 100/100; five source-equivalence tests pass |

## Constraints

- `upstream/README.md` says the ImageNet-C experiment requires offline ViT
  entropy arrays that are not supplied.  It is explicitly outside the executed
  scope, not replaced by a proxy.
- The ImageNet-C result remains unavailable, not a failed local run: the
  author-required entropy arrays are neither released nor downloadable from the
  pinned source.

## Next action

Create the Trackio logbook and capture the verified full command with clean
relative paths; then run the publication gate (including a secret scan).  Do
not publish until the Hugging Face Space quota resets.
