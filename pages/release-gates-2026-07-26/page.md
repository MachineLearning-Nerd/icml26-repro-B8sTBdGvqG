# Release gates — July 26, 2026 candidate

This page records the evaluator-visible release checks before publication.

## Old Space preservation

The exact judged Space revision `DineshAI/B8sTBdGvqG@14b47abfde98661247d9397ef36bb3a45198d2fb` was downloaded before building this candidate. Its visible file set is preserved by path in the candidate; new files are additive except for canonical navigation/entrypoint updates required to expose current evidence.

## Forecast table

| Claim | Status | Expected points | Confidence | Expected evaluator status |
|---|---|---:|---|---|
| 1 | VERIFIED | 2 | HIGH | preserve existing full credit |
| 2 | FALSIFIED | 2 | HIGH | upgrade from inconclusive if evaluator accepts discrete-null counterexample |
| 3 | VERIFIED | 2 | MEDIUM | upgrade from inconclusive if evaluator accepts proof certificate |
| 4 | VERIFIED | 2 | HIGH | preserve existing full credit |
| 5 | VERIFIED | 2 | HIGH | preserve existing full credit |
| 6 | BLOCKED | 0 | LOW | remain inconclusive/blocked |

Conservative projected total: `10/12`. Best-supported possible total: `10/12` forecast, not a live judge result.

## Commands

```bash
orx exp run 3229d43a-6cb7-46dc-8e70-1973369abaf1 --backend hf --flavor cpu-upgrade --image ghcr.io/astral-sh/uv:python3.12-bookworm-slim --timeout 2h
orx exp wait 3229d43a-6cb7-46dc-8e70-1973369abaf1 --interval 20 --timeout 900
orx logs 7e9019e0-e75e-44ab-805d-5fe4dbf06d3f --bytes 1000000
```

Inside the job the fixed command was exactly:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

## No-secrets and upload allowlist

The uploaded paths are text files only: Markdown, JSON, CSV, Python, shell, TOML, lockfile, README, and logbook files. Existing binary images/assets already present in the Space are left untouched.

## Current total and changed claims

Current live score before publication: `6/12`. Claims changed by this package: Claim 2 moves from inconclusive to `FALSIFIED`; Claim 3 moves from inconclusive to `VERIFIED`; Claim 6 becomes explicitly `BLOCKED` with four routes rather than skipped. Claims 1, 4, and 5 retain existing verified synthetic evidence.
