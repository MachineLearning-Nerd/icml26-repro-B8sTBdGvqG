# Claim 1 — Faster shift detection


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_a8fb95f6609c", "created_at": "2026-07-17T12:15:22+00:00", "title": "C1 full-source evidence"}
-->
**C1 reproduced on the complete released synthetic suite.**

Primary source configuration: 100 independent `N(0,1) -> N(1,1)` streams, 2,000 calibration observations, and 1,000 test observations. Conditional CTM and standard growing-reference CTM both detected 100/100 streams. Conditional CTM crossed at median **21** observations, versus **31** for the standard CTM.

The three source bias settings, three delayed-shift settings (with the source warm-up and `T=4,500`), and three gradual-drift settings all independently had lower conditional median post-shift delay. In the fixed-reference contamination control, late shifted observations had mean conditional ECDF value **0.7434** versus **0.5551** for growing-reference randomized p-values; this is the claimed dilution mechanism.

The verifier re-aggregates raw crossing records without importing the martingale implementation and passed all C1 checks.
