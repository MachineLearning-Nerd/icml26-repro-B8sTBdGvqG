# Claim 2 — Validity, power, and delay


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_ac03393b6dd0", "created_at": "2026-07-17T12:15:38+00:00", "title": "C2 full-source evidence"}
-->
**C2 reproduced empirically at the released finite synthetic scope.**

At nominal level 5%, the full source null grid runs 100 streams for each of 11 reported calibration sizes (`0, 500, ..., 5000`) and a 20,000-observation horizon. Conditional CTM's observed Type-I rate was **0–1%** in every configuration. The intentionally uncorrected no-DKW fixed-reference control is a falsifier: it rejected **88%** of the zero-calibration streams and remained elevated at several smaller calibration sizes.

An independent increasing-horizon check (`T=100, 300, 1000, 3000`) detected all 100 mean-shift streams at each horizon; median crossings were 18–22 observations. The source AR(1) setting also had 100% conditional detection with median crossing 12.

This is executed finite-sample evidence for the claim's observable validity/power/delay behavior. It explicitly does **not** present a simulation as a proof of the paper's asymptotic theorem.
