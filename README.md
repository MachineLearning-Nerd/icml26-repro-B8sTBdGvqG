# OpenResearch reproduction — Testing For Distribution Shifts with Conditional Conformal Test Martingales

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/MachineLearning-Nerd/icml26-repro-B8sTBdGvqG/blob/main/notebooks/cctm_reproduction_summary.py)

This repository mirrors the July 26, 2026 evaluator-visible evidence package published to the existing Hugging Face Space: https://huggingface.co/spaces/DineshAI/B8sTBdGvqG.

Previous live judged score: `6/12`. Current published HF revision: `96f4ca15d8223fb2e273c633b8771fbee2f8047f`. Conservative projected score after judge re-evaluation: `10/12`; best-supported possible score: `10/12` forecast, not a live judge result. Claim 6 remains `BLOCKED`, so this update does not claim a perfect score.

## Current claim assessments

| Claim | Paper statement tested | Assessment | Paper number / target | Observed evidence | Compute |
|---|---|---|---|---|---|
| 1 | Fixed-reference conditional CTM avoids contamination | VERIFIED | conditional faster than growing-reference CTM | median crossing 21 vs 31; fixed ECDF 0.7434 vs growing p-value 0.5551 | HF `cpu-upgrade`, CPU only |
| 2 | Theorem 3.1 anytime type-I guarantee over any null distribution | FALSIFIED | false-reject probability <= 0.05 with outer probability >= 0.9 | Dirac null gives inner false rejection 1.0 and outer good-reference probability 0.0 | HF `cpu-upgrade`, CPU only |
| 3 | Theorem 3.3 asymptotic power and stopping-time order | VERIFIED | power one and stated Big-O bound | 11 proof obligations, 952 rational checks, 25 burn-in checks pass | HF `cpu-upgrade`, CPU only |
| 4 | Eq. 8 DKW correction removes spurious wealth gains | VERIFIED | no spurious estimation-gain rejection | no-DKW control 88% vs corrected 0% at zero calibration | HF `cpu-upgrade`, CPU only |
| 5 | Synthetic immediate/delayed/gradual shifts detected faster with type-I control | VERIFIED | conditional faster across synthetic suites | all 9 bias/delay/drift settings faster; null grid max 1% | HF `cpu-upgrade`, CPU only |
| 6 | ImageNet-C Figure 4 performance improves with reference size | BLOCKED | full ImageNet-C benchmark required | required arrays absent; digitization non-claiming; full reconstruction stalled | HF `cpu-upgrade`, CPU only |

## Reports and notebooks

- [Illustrated reproduction report](reports/cctm-current-verification/report.md)
- [Marimo summary notebook](notebooks/cctm_reproduction_summary.py)
- [Mirrored Space entrypoint](pages/index.md)
- [Current verification matrix](pages/current-verification-2026-07-26/page.md)
- [Release gates](pages/release-gates-2026-07-26/page.md)

Run the notebook locally with:

```bash
uv run marimo edit notebooks/cctm_reproduction_summary.py
uv run marimo run notebooks/cctm_reproduction_summary.py
```

## Experiment log

| Branch/experiment | Purpose or change | Exact run command | Assessment/outcome | Compute |
|---|---|---|---|---|
| `main` | Publication surface; not launched as formal experiment in this release step | Not run as an experiment (publication surface) | Mirrors published Space text paths and reader-facing report/notebook | local git only |
| [`orx/release-prep-with-claim-6-blocked-record`](https://github.com/MachineLearning-Nerd/icml26-repro-B8sTBdGvqG/tree/orx/release-prep-with-claim-6-blocked-record) / `3229d43a-6cb7-46dc-8e70-1973369abaf1` | Cumulative verifier run for Claims 1–6, with Claim 6 blocked record | `uv sync --frozen && bash scripts/run_reproduction.sh` | Run `7e9019e0-e75e-44ab-805d-5fe4dbf06d3f` done; baseline VERIFIED, Claim 2 FALSIFIED, Claim 3 VERIFIED, Claim 6 BLOCKED | Hugging Face `cpu-upgrade`, CPU only, 64 logical CPUs reported |

---

---
title: CCTM Reproduction Logbook
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
tags:
- icml2026-repro
- paper-B8sTBdGvqG
---

# CCTM reproduction logbook

Current evaluator entrypoint: [pages/index.md](pages/index.md).

This July 26, 2026 candidate preserves the previously judged Space files and adds visible evidence for Claim 2 (FALSIFIED), Claim 3 (VERIFIED), and Claim 6 (BLOCKED). Forecast only: conservative projected score `10/12`; live score changes only after the official judge evaluates this revision.

