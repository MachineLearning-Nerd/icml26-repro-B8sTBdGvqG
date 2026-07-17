# Status — Conditional Conformal Test Martingales

## Current step

Source audit and clean-room, source-equivalent CPU runner in progress.

## Claims and evidence plan

| Claim | Required full-scope evidence | State |
|---|---|---|
| C1 | 100-repetition N(0,1)→N(1,1) power/detection-delay comparison, delayed-shift control, and the source's fixed-vs-growing-reference mechanism check | pending execution |
| C2 | 100-repetition null sweep over the released calibration-size grid and horizon, plus increasing-horizon power/delay checks and independent transition tests | pending execution |

## Constraints

- `upstream/README.md` says the ImageNet-C experiment requires offline ViT
  entropy arrays that are not supplied.  It is explicitly outside the executed
  scope, not replaced by a proxy.
- Another session currently occupies all four CPU cores with Bitwen.  Do not
  start the full synthetic sweep until that job has finished.

## Next action

Finish source-equivalent runner tests, then execute the complete released
synthetic suite from the paper's configuration when CPU capacity is available.

