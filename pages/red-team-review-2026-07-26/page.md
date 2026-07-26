# Evaluator-blind red-team review — July 26, 2026

Reviewer constraint: use only the downloaded candidate artifact and start from `pages/index.md`; do not use repository-local knowledge or hidden OpenResearch paths.

Files opened during traversal:

1. `pages/index.md`
2. `pages/current-verification-2026-07-26/page.md`
3. `pages/claim-2-falsified-theorem-31/page.md`
4. `pages/claim-3-verified-theorem-33/page.md`
5. `pages/claim-6-blocked-imagenet-c/page.md`
6. `pages/release-gates-2026-07-26/page.md`
7. Linked raw evidence under `evidence/claim_2/`, `evidence/claim_3/`, `evidence/claim_6/`, `evidence/synthetic/`, and `evidence/runs/7e9019e0-e75e-44ab-805d-5fe4dbf06d3f/`.
8. Linked verifier code under `code/repro/` and `code/scripts/run_reproduction.sh`.

Red-team conclusions:

| Claim | Could locate exact claim? | Could locate code? | Could locate raw data? | Could locate checker/control? | Reviewer conclusion |
|---|---|---|---|---|---|
| 1 | yes | yes | yes | yes | VERIFIED evidence visible; existing full-credit result preserved. |
| 2 | yes | yes | yes | yes | FALSIFIED evidence visible; discrete-null witness directly contradicts theorem quantifiers. |
| 3 | yes | yes | yes | yes | VERIFIED proof-certificate evidence visible; remaining risk is proof-formalism acceptance. |
| 4 | yes | yes | yes | yes | VERIFIED DKW negative-control evidence visible. |
| 5 | yes | yes | yes | yes | VERIFIED synthetic shift-suite evidence visible. |
| 6 | yes | yes | yes | yes | BLOCKED record visible; no unsupported ImageNet-C verification claim is made. |

Result: release navigation is evaluator-visible. No missing visibility-matrix cell remained after link validation.
