# ICML 2026 reproduction — Conditional Conformal Test Martingales

This repository is an independent, claim-by-claim audit of [Testing For Distribution Shifts with Conditional Conformal Test Martingales](https://arxiv.org/abs/2602.13848). It preserves the original reproduction package and adds a clear evidence ledger, branch map, source manifest, citation, and reproducibility gate.

The repository was formerly named `icml26-repro-B8sTBdGvqG`. The final public name is `icml26-conditional-conformal-test-martingales`.

## Paper

- **Title:** *Testing For Distribution Shifts with Conditional Conformal Test Martingales*
- **Authors:** Shalev Shaer, Yarin Bar, Drew Prinster, and Yaniv Romano
- **arXiv:** [2602.13848](https://arxiv.org/abs/2602.13848) (v2, 12 June 2026)
- **OpenReview:** [B8sTBdGvqG](https://openreview.net/forum?id=B8sTBdGvqG)
- **Official implementation:** [`shaersh/cctm`](https://github.com/shaersh/cctm), pinned at commit `a9feb795d9fa98cc1d0c075f8f08a5c510c7a844`

The paper proposes a conditional conformal test martingale that keeps a fixed reference set, accounts for finite-reference ECDF error with a confidence band, and uses online betting to detect distribution shifts. The paper claims finite-sample anytime validity, asymptotic power, bounded expected detection delay, and empirical gains on synthetic and ImageNet-C streams.

## Current audit verdict

These are scoped reproduction judgments, not an author endorsement or a new official ICML score.

| Claim | Paper statement | Verdict | How the verdict is produced |
|---|---|---|---|
| C1 | Fixed-reference conditional CTM detects shifts faster than the growing-reference CTM | `VERIFIED_SCOPED` | Full released synthetic suites, source-equivalence tests, and independent re-aggregation |
| C2 | Theorem 3.1 gives an anytime type-I guarantee for **any** null distribution | `FALSIFIED_AS_WRITTEN` | A Dirac-null counterexample satisfies the printed assumptions; the displayed and released processes cross the rejection threshold |
| C3 | Theorem 3.3 gives asymptotic power one and the stated stopping-time order | `VERIFIED_PROOF_AUDIT` | Corrected symbolic certificate, 11 obligations, 952 rational checks, 25 burn-in checks, and an independent checker |
| C4 | The DKW correction prevents spurious wealth gains | `VERIFIED_SCOPED` | Corrected versus no-DKW synthetic control; the no-DKW control rejects 88% at zero calibration points while the corrected method rejects 0% |
| C5 | Conditional CTM improves synthetic shift power/delay while controlling false alarms | `VERIFIED_SCOPED` | All nine released bias, delay, and drift settings, plus the 11-point null grid and independent re-aggregation |
| C6 | ImageNet-C Figure 4 improves with reference size and for Blur/Weather groups | `BLOCKED` | Required entropy arrays are absent; source-figure digitization is non-claiming; full reconstruction stalled; no valid full-scope counterexample was found |

The finite synthetic C2 checks remain useful empirical evidence, but they do not prove Theorem 3.1. The C2 theorem verdict is based on the explicit assumption-matched counterexample. Likewise, C3 audits a corrected proof path; it is not a proof-assistant formalization of every theorem used by the paper.

The historical evaluator-visible package reported a live score of `6/12` at Hugging Face revision `14b47abfde98661247d9397ef36bb3a45198d2fb`. A later package was published at revision `96f4ca15d8223fb2e273c633b8771fbee2f8047f` with a `10/12` projected score. That projection is historical forecast data, not a current judge result and not claimed here as a new score.

## How claims are produced

The complete claim-to-evidence ledger is in [`CLAIM_EVIDENCE.md`](CLAIM_EVIDENCE.md). The short production paths are:

| Claim | Producer | Stored evidence | Independent check |
|---|---|---|---|
| C1, C4, C5 | `code/repro/run_full_synthetic.py` | `evidence/synthetic/full_synthetic_summary.json` | `code/repro/verify_full_synthetic.py` and `evidence/synthetic/independent_verification.json` |
| C2 | `code/repro/run_claim2_counterexample.py` | `evidence/claim_2/prior_run_raw_results.json`, trajectory, and controls | `verify_claim2_counterexample.py`, `independent_check_claim2.py`, and frozen verifier |
| C3 | `code/repro/verify_claim3_proof.py` | `evidence/claim_3/proof_certificate.json` | `independent_check_claim3.py`, contract verifier, and frozen verifier |
| C6 | release audit, figure digitizer, stall recorder, and falsification route | `evidence/claim_6/*` | four route checkers and `final_blocked_verifier_output.json` |

All claim judgments are fail-closed: a missing input or unresolved assumption does not become a positive result. See [`evidence/claim_summary.json`](evidence/claim_summary.json) for the machine-readable summary.

## Repository and branches

The original `orx/*` branches are renamed to purpose-based names while their distinct evidence histories are preserved. Every branch is explained in [`BRANCH_AUDIT.md`](BRANCH_AUDIT.md), including its original name, original tip, purpose, and final name. The final package uses `main` plus evidence, experiment, audit, proof, fix, baseline, counterexample, and release branches.

The pinned source, paper-version, dataset, environment, and historical-run identifiers are listed in [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md).

## Reproduce the focused audit

The repository contains the already-generated evidence artifacts. A fresh checkout can run the lightweight checks without downloading ImageNet:

```bash
cd code
uv sync --frozen
uv run pytest -q
mkdir -p /tmp/cctm-claim2
uv run python repro/run_claim2_counterexample.py \
  --output-dir /tmp/cctm-claim2
uv run python repro/verify_claim2_counterexample.py \
  --artifact-dir /tmp/cctm-claim2
uv run python repro/independent_check_claim2.py \
  --artifact-dir /tmp/cctm-claim2
mkdir -p /tmp/cctm-claim3
uv run python repro/verify_claim3_proof.py \
  --artifact-dir /tmp/cctm-claim3
uv run python repro/independent_check_claim3.py \
  --artifact-dir /tmp/cctm-claim3
uv run python repro/verify_claim6_blocked_routes.py \
  --artifact-dir ../evidence/claim_6
cd ..
python3 code/repro/verify_final.py
```

The historical full command is `cd code && bash scripts/run_reproduction.sh`. It reproduces the synthetic and theorem evidence, then records Claim 6 as blocked because the official ImageNet-C entropy arrays are not available. It should not be read as a promise that the missing benchmark can run locally.

## Layout

- `code/repro/` — clean-room producers, checkers, tests, and the final gate.
- `evidence/` — durable JSON/CSV outputs and claim contracts.
- `pages/` and `reports/` — reader-facing logbook and historical report.
- `BRANCH_AUDIT.md` — branch purpose and rename map.
- `CLAIM_EVIDENCE.md` — claim-to-evidence production paths and limitations.
- `SOURCE_MANIFEST.md` — pinned sources, versions, hashes, and provenance.
- `CITATION.cff` — software and paper citation metadata.

## Citation

```bibtex
@article{shaer2026conditional_conformal_test_martingales,
  title   = {Testing For Distribution Shifts with Conditional Conformal Test Martingales},
  author  = {Shaer, Shalev and Bar, Yarin and Prinster, Drew and Romano, Yaniv},
  journal = {arXiv preprint arXiv:2602.13848},
  year    = {2026},
  doi     = {10.48550/arXiv.2602.13848}
}
```

## Thank you

Thank you to Shalev Shaer, Yarin Bar, Drew Prinster, and Yaniv Romano for sharing the paper, implementation, and enough experimental detail to make a careful independent audit possible. This repository is grateful for that release and records both its reproducible evidence and its unresolved data limitations.

## Attribution

The maintained repository and approved cleanup commits are attributed to `MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>`. The paper authors retain authorship of the paper and its scientific claims.
