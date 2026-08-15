# Source and provenance manifest

This manifest separates primary-source facts, pinned implementation inputs, generated evidence, and historical publication records.

## Paper

| Field | Value |
|---|---|
| Title | *Testing For Distribution Shifts with Conditional Conformal Test Martingales* |
| Authors | Shalev Shaer; Yarin Bar; Drew Prinster; Yaniv Romano |
| arXiv | [`2602.13848`](https://arxiv.org/abs/2602.13848), v2, 2026-06-12 |
| HTML source | [`arxiv.org/html/2602.13848`](https://arxiv.org/html/2602.13848) |
| OpenReview | [`B8sTBdGvqG`](https://openreview.net/forum?id=B8sTBdGvqG) |
| Paper source snapshot used by claim contracts | `ef9032cb84ff680f5b31cd19e67b2991839e669f7ce0f8d2cbaabd1120d273a3` |
| arXiv source archive used by the Figure 4 audit | `850ea40712686ee84543348bf39550ead19e6240ad5f085c07654ef3ed1e4b4e` from `https://export.arxiv.org/e-print/2602.13848` |

The arXiv abstract states that the method uses a fixed null reference, accounts for finite-reference estimation error, and targets anytime validity, power one, and bounded expected delay. The HTML paper anchors Theorem 3.1, Theorem 3.3, the synthetic figures, and the ImageNet-C protocol used in the claim ledger.

## Official implementation

| Field | Value |
|---|---|
| Repository | [`shaersh/cctm`](https://github.com/shaersh/cctm) |
| Pinned commit | `a9feb795d9fa98cc1d0c075f8f08a5c510c7a844` |
| Synthetic protocol | 100 repetitions; calibration sizes 0, 500, …, 5,000; immediate, delayed, gradual, clipping, AR(1), and pairwise suites |
| ImageNet-C model | `timm/vit_base_patch16_224` |
| ImageNet-C scope | Severity 5; 15 corruption types; 37,500 test examples; 10 seeded realizations; reference sizes 100, 500, 4,000; warm-up 50 |
| Missing required data | 12,500 clean entropy values plus 15 × 37,500 corrupted entropy arrays and raw Figure 4 tables |

## Local environment

The executable environment is pinned by `code/pyproject.toml` and `code/uv.lock`: Python 3.12, NumPy 2.3.2, SciPy 1.16.1, SymPy 1.14.0, PyTorch 2.7.1 CPU, torchvision 0.22.1 CPU, timm 1.0.19, and pytest 8.4.1. The clean-room implementation is under `code/repro/`; the committed `code/repro/reference_ctm.py` contains only the upstream recurrences exercised by the source-equivalence tests. The root `evidence/` tree contains the durable outputs used by the final documentation.

## Evidence artifacts

| Evidence | Producer or checker | Scope |
|---|---|---|
| `evidence/synthetic/full_synthetic_summary.json` | `code/repro/run_full_synthetic.py` | Full released synthetic protocol |
| `evidence/synthetic/independent_verification.json` | `code/repro/verify_full_synthetic.py` | Independent C1/C4/C5 aggregation |
| `evidence/claim_2/*` | Claim 2 producer, verifier, independent checker | Dirac-null theorem counterexample |
| `evidence/claim_3/*` | Claim 3 certificate and independent checker | Corrected proof audit |
| `evidence/claim_6/*` | Four route producers and checkers | Missing-data, digitization, stall, and falsification audit |
| `evidence/runs/7e9019e0-e75e-44ab-805d-5fe4dbf06d3f/*` | Historical remote run record | July 26, 2026 evaluator-visible package |

The evidence files are not a substitute for missing benchmark inputs. In particular, source-figure CSVs and images in Claim 6 record plotted evidence only and are intentionally not promoted to benchmark reproduction.

## Historical publication provenance

- Hugging Face Space: `DineshAI/B8sTBdGvqG`.
- Previous live judged score: `6/12` at revision `14b47abfde98661247d9397ef36bb3a45198d2fb`.
- Later published candidate revision: `96f4ca15d8223fb2e273c633b8771fbee2f8047f`.
- Historical experiment/run identifiers are preserved in the evidence log and are not represented as a current official score.
- The original `orx/*` branch names recorded in historical metadata are mapped to final purpose-based branches in [`BRANCH_AUDIT.md`](BRANCH_AUDIT.md).

## Citation and thanks

The paper citation is in [`CITATION.cff`](CITATION.cff) and the README. Thank you to Shalev Shaer, Yarin Bar, Drew Prinster, and Yaniv Romano for releasing the paper and implementation and for making this independent audit possible.
