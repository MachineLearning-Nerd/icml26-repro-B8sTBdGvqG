# Current verification package — CCTM reproduction

This is the current evaluator entrypoint for the July 26, 2026 release candidate. It supersedes the earlier two-claim logbook pages while keeping those historical pages reachable.

Previous live judged score: `6/12` at HF revision `14b47abfde98661247d9397ef36bb3a45198d2fb`.

Conservative projected score range after this publication: `10/12` if the live evaluator accepts the new visible Claim 2 and Claim 3 evidence and preserves existing Claim 1/4/5 credit. This is a forecast, not a judge result.

Best-supported possible new score: `10/12` forecast. Claim 6 remains `BLOCKED`, so this package does not honestly support `12/12`.

Fixed command for every node:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

Remote cumulative run used for this package:

- Experiment: `3229d43a-6cb7-46dc-8e70-1973369abaf1`
- Run: `7e9019e0-e75e-44ab-805d-5fe4dbf06d3f`
- Branch: `orx/release-prep-with-claim-6-blocked-record`
- Git SHA: `9d56f3e05e10e5f0cd57b6bd8bfef419d909612a`
- Backend/flavor: Hugging Face `cpu-upgrade`, CPU only, image `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- CPU allocation reported by the run: 64 logical CPUs; expected useful cores: 4 for synthetic/theorem checks, 1 for Claim 6 audit routes
- Raw run log: [evidence/runs/7e9019e0-e75e-44ab-805d-5fe4dbf06d3f/orx_log.txt](../../evidence/runs/7e9019e0-e75e-44ab-805d-5fe4dbf06d3f/orx_log.txt)

## Claim summary

| Claim | Current points | Possible points | Confidence | Evidence status | Basis and remaining risk |
|---|---:|---:|---|---|---|
| 1 | 2 | 2 | HIGH | VERIFIED | Fixed-reference contamination mechanism and synthetic regression preserved: primary median crossing 21 vs 31; fixed-reference late ECDF 0.7434 vs growing-reference p-value 0.5551. |
| 2 | 0 | 2 | HIGH | FALSIFIED | Theorem 3.1 says any null distribution; a Dirac null satisfies the stated assumptions but ordinary PIT makes the martingale cross with probability 1. Independent checker reconstructs the witness. |
| 3 | 0 | 2 | MEDIUM | VERIFIED | Machine-checkable corrected symbolic derivation covers asymptotic power and stopping-time order; independent checker passes 952 rational-grid and 25 burn-in checks. Risk: evaluator may require a different proof formalism. |
| 4 | 2 | 2 | HIGH | VERIFIED | DKW correction preserved: no-DKW negative control rejects 88% at zero calibration while corrected conditional CTM rejects 0%. |
| 5 | 2 | 2 | HIGH | VERIFIED | Full released synthetic protocol preserved: all nine bias/delay/drift settings show faster conditional CTM with 0–1% null rejection rates. |
| 6 | 0 | 0 | LOW | BLOCKED | Official entropy arrays are absent; source-figure digitization is not independent benchmark evidence; full reconstruction stalled; falsification route found no valid full-scope counterexample. |

## Evaluator-visible visibility matrix

| Claim | Canonical page | Code visible | Data inline | Raw link | Checker | Control | Exact claim tested | Reviewer verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | [Current verification](#/current-verification-2026-07-26) | yes: `code/repro/run_full_synthetic.py`, `code/repro/verify_full_synthetic.py` | yes: median 21 vs 31, fixed 0.7434 vs growing 0.5551 | `evidence/synthetic/full_synthetic_summary.json` | independent synthetic re-aggregation | growing-reference contamination control | fixed-reference avoids contamination | VERIFIED |
| 2 | [Claim 2 falsification](#/claim-2-falsified-theorem-31) | yes: `code/repro/run_claim2_counterexample.py`, verifier and independent checker | yes: inner false-reject probability 1.0, required <=0.05; outer good-reference probability 0.0, required >=0.9 | `evidence/claim_2/prior_run_raw_results.json`, `prior_run_trajectory.csv` | `prior_run_verifier_output.json`, `prior_run_independent_checker_output.json` | randomized PIT repair and reverse-direction bet | Theorem 3.1 universal type-I statement | FALSIFIED |
| 3 | [Claim 3 proof certificate](#/claim-3-verified-theorem-33) | yes: `code/repro/verify_claim3_proof.py`, `code/repro/independent_check_claim3.py` | yes: 11 obligations passed, 952 rational grid checks, 25 burn-in checks | `evidence/claim_3/proof_certificate.json` | `verifier_output.json`, `independent_checker_output.json` | detects unconstrained-maximizer and tail-rate printed proof errors | Theorem 3.3 asymptotic power and stopping-time order | VERIFIED |
| 4 | [Current verification](#/current-verification-2026-07-26) | yes: synthetic runner/verifier code | yes: naive no-DKW rejection 88% vs corrected 0% at n=0 | `evidence/synthetic/full_synthetic_summary.json` | independent synthetic re-aggregation | no-DKW control | Equation 8 DKW correction suppresses estimation-gain artifacts | VERIFIED |
| 5 | [Current verification](#/current-verification-2026-07-26) | yes: synthetic runner/verifier code | yes: all 9 bias/delay/drift settings faster and type-I max 1% | `evidence/synthetic/full_synthetic_summary.json` | independent synthetic re-aggregation | null type-I grid and no-DKW control | synthetic immediate/delayed/gradual shift claims | VERIFIED |
| 6 | [Claim 6 blocked record](#/claim-6-blocked-imagenet-c) | yes: release audit, digitizer, stall recorder, falsification route, final verifier | yes: 16 required arrays absent; route-2 plotted Blur/Weather ratios >1 for n>=500 but non-claiming; 15 full jobs stalled/cancelled | `evidence/claim_6/*` | `final_blocked_verifier_output.json` and route checkers | missing-data/proxy/off-scope invalid falsification controls | ImageNet-C Figure 4 full-scope benchmark | BLOCKED |


## Direct raw outputs from the HF run

The HF log prints these terminal markers:

```text
BASELINE_VERDICT=VERIFIED
CLAIM2_VERDICT=FALSIFIED
CLAIM3_VERDICT=VERIFIED
CLAIM6_FINAL_VERDICT=BLOCKED
```

The same log also prints the pinned environment from `uv.lock`, the Git SHA, selected backend/flavor, CPU allocation, deterministic seeds where stochastic evidence is used, raw JSON/CSV snippets, independent checker output, and negative-control output.

## Historical pages

The prior judged pages remain reachable below for preservation. The old page titled `Claim 2 — Validity, power, and delay` is now a historical rejected baseline for theorem evidence: it provided empirical consistency only and was judged inconclusive for Theorems 3.1 and 3.3. The current verifier is this page plus the three new claim pages linked above.
