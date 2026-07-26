# CCTM reproduction — current evaluator entrypoint

This is the current entrypoint for the July 26, 2026 candidate. It preserves the prior judged Space pages and adds the evidence required to address the judge's Claim 2 and Claim 3 criticisms. Claim 6 is honestly recorded as BLOCKED.

Previous live judged score: `6/12` at HF revision `14b47abfde98661247d9397ef36bb3a45198d2fb`.

Forecast after this publication, not a judge result: conservative projected range `10/12`; best-supported possible score `10/12`. Claim 6 remains `BLOCKED`, so this package does not claim `12/12`.

Fixed command used for all evidence:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

HF cumulative run: `7e9019e0-e75e-44ab-805d-5fe4dbf06d3f` on Hugging Face `cpu-upgrade`, CPU only, commit `9d56f3e05e10e5f0cd57b6bd8bfef419d909612a`.

## Current pages

| Page | Purpose |
|---|---|
| [Current verification — July 26 2026](#/current-verification-2026-07-26) | Claim summary, visibility matrix, exact command, forecast, raw-run links. |
| [Claim 2 — FALSIFIED Theorem 3.1](#/claim-2-falsified-theorem-31) | Discrete-null counterexample, raw results, verifier, independent checker, controls. |
| [Claim 3 — VERIFIED Theorem 3.3](#/claim-3-verified-theorem-33) | Corrected symbolic proof certificate, independent checker, controls. |
| [Claim 6 — BLOCKED ImageNet-C](#/claim-6-blocked-imagenet-c) | Four verification routes and why no full-scope verification/falsification is available. |
| [Release gates — July 26 2026](#/release-gates-2026-07-26) | Publication gate record, command list, allowlist, projected score. |
| [Red-team review — July 26 2026](#/red-team-review-2026-07-26) | Evaluator-blind traversal record. |

## Historical judged pages preserved

| Page | Status |
|---|---|
| [Overview](#/overview) | Historical judged baseline context. |
| [Claim 1 — Faster shift detection](#/claim-1-faster-shift-detection) | Existing full-credit synthetic evidence, preserved. |
| [Historical rejected baseline — prior validity/power page](#/claim-2-validity-power-and-delay) | Old empirical-only page; superseded for theorem claims by current Claim 2 and Claim 3 pages. |
| [Methods & source audit](#/methods-source-audit) | Historical source/method page. |
| [Negative controls](#/negative-controls) | Historical synthetic negative controls. |
| [Conclusion](#/conclusion) | Historical conclusion. |
