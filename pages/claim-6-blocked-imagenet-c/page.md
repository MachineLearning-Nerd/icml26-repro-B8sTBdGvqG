# Claim 6 — BLOCKED: ImageNet-C Figure 4

Verdict: `BLOCKED`.

Exact claim audited: on ImageNet-C severity 5 with entropy scores from timm ViT-B/16, using all 15 corruption types, 37,500-example streams, 10 realizations, and `alpha=0.05`, detection performance improves with reference set size `n >= 500`, and larger-shift Blur/Weather corruption groups have median standard/conditional rejection-time ratio above one.

This package does not claim Claim 6 as verified or falsified.

Four verification-oriented routes were completed:

1. Official release/data-identity audit: `BLOCKED`. The source release requires 16 `.npy` entropy files and provides none. It also has a CLI negative control: `args.gamma` is referenced but `--gamma` is not declared.
2. Source-figure digitization: `BLOCKED`. The pinned arXiv figure visually encodes the claimed trend. Digitized Blur/Weather ratios for `n>=500` are above one, but this is only the authors' plotted evidence, not an independent ImageNet-C benchmark run.
3. Full reconstruction attempt: `BLOCKED`. Fifteen HF `cpu-upgrade` component jobs were attempted and later observed as cancelled/stalled before clean or corruption inference checkpoints; no full-scope numerical result was produced.
4. Mandatory falsification search: `BLOCKED`. Missing data, reduced smoke subsets, stalled jobs, and off-scope plotted points were all rejected as invalid falsifications. No valid full-scope counterexample was found.

Key route-2 plotted values from the source figure audit:

- Blur ratios: `n=500 -> 1.2804`, `n=1000 -> 1.3735`, `n=4000 -> 1.5830`.
- Weather ratios: `n=500 -> 1.4013`, `n=1000 -> 1.5438`, `n=4000 -> 1.6895`.

These values are useful for auditing the paper figure, but they do not satisfy the independent-reproduction requirement.

Raw evidence:

- [claim contract](../../evidence/claim_6/claim_contract.json)
- [official release audit](../../evidence/claim_6/release_audit.json)
- [independent release audit](../../evidence/claim_6/independent_release_audit.json)
- [route 2 figure audit](../../evidence/claim_6/route2_figure_audit.json)
- [route 2 power CSV](../../evidence/claim_6/route2_power_crossings.csv)
- [route 2 ratio CSV](../../evidence/claim_6/route2_ratio_points.csv)
- [route 3 full reconstruction stall record](../../evidence/claim_6/route3_full_reconstruction_stall.json)
- [route 4 falsification attempt](../../evidence/claim_6/route4_falsification_attempt.json)
- [final blocked verifier output](../../evidence/claim_6/final_blocked_verifier_output.json)
- [method](../../evidence/claim_6/method.md), [source audit](../../evidence/claim_6/source_audit.md), [limitations](../../evidence/claim_6/limitations.md)

Visible code:

- [release audit](../../code/repro/audit_claim6_release.py)
- [independent release checker](../../code/repro/independent_check_claim6_release.py)
- [figure digitizer](../../code/repro/digitize_claim6_figure.py)
- [figure independent checker](../../code/repro/independent_check_claim6_figure.py)
- [route-2 verifier](../../code/repro/verify_claim6_route2.py)
- [route-2 fail-closed checker](../../code/repro/check_claim6_route2_fail_closed.py)
- [stall recorder](../../code/repro/record_claim6_full_run_stall.py)
- [falsification route](../../code/repro/run_claim6_falsification_route.py)
- [final blocked verifier](../../code/repro/verify_claim6_blocked_routes.py)

Final verifier passed = `true`; confidence = `LOW`.
