# Claim 6 source audit

## Exact paper statement

The primary HTML source was retrieved from
`https://ar5iv.labs.arxiv.org/html/2602.13848` on
2026-07-24T15:36:32Z with an explicit
`OpenResearch-Reproduction/1.0` user agent. Its SHA-256 is
`ef9032cb84ff680f5b31cd19e67b2991839e669f7ce0f8d2cbaabd1120d273a3`.

Figure 4 is `S4.F4`; the reference-size interpretation is `S4.SS2.p2`; the
ImageNet-C implementation details are in the appendix section corresponding to
TeX lines 1567–1579. The experiment uses:

- all 15 ImageNet-C corruptions at severity 5;
- clean-reference sizes 100, 500, and 4,000 in the power panel;
- entropy of a fixed pretrained `timm` `vit_base_patch16_224`;
- a 37,500-example test stream and 10 seeded realizations;
- `alpha=0.05`, warmup 50, ONS diameter 0.5, clipping constant 0.05, and
  smoothing `1e-6`.

The paper says conditional CTM outperforms standard CTM for `n>=500`. Its
ratio panel defines standard/conditional median rejection time, so values
above one favor conditional CTM, and highlights Blur and Weather as
larger-shift groups.

## ArXiv source package

The arXiv source archive was retrieved from
`https://export.arxiv.org/e-print/2602.13848` with the same explicit user
agent. Its SHA-256 is
`850ea40712686ee84543348bf39550ead19e6240ad5f085c07654ef3ed1e4b4e`.
It contains the two Figure 4 PNGs but no raw CSV, JSON, NumPy array, inference
script, or tabulated Figure 4 values:

- `power_vs_step_by_calibsize_logx_w50.png`,
  SHA-256 `3ec26c59a6101229a024cd6493a4db55cffb6b35700ee9b50281c432b5e6600c`;
- `rejection_time_ratio_vs_ctm_by_group_logy_logx.png`,
  SHA-256 `842f96dc197d8dd1cc24d59d722024f33e5a83d6876a86326436874dee5be96a`.

## Official code release

The official `shaersh/cctm` repository is pinned at
`a9feb795d9fa98cc1d0c075f8f08a5c510c7a844`. Its complete Git tree has 19
blobs, no release assets, one branch (`main`), and no `.npy`, CSV, or Figure 4
raw-result files. GitHub code search finds the required entropy filenames only
as prose/code references in `README.md` and `sudden_shift_experiment.py`.

The release documents one clean `holdout_ents.npy` and 75 corruption arrays
(five severities by 15 corruptions). The companion notebook says the clean
array has 12,500 values and each corruption array has 37,500 values. None is
published and there is no acquisition or inference script.

The documented sudden-shift CLI also cannot run as released: it reads
`args.gamma` and constructs `ExperimentConfig(gamma=args.gamma)`, but never
declares `--gamma`. This causes an `AttributeError` before the missing arrays
are even opened. That defect blocks the release path but is not evidence
against Figure 4.

## Public reconstruction inputs

The raw-image inputs are potentially reconstructable:

- `WNJXYK/TTA-ImageNet-C`, revision
  `bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7`, is public and ungated;
- `ILSVRC/imagenet-1k`, revision
  `49e2ee26f3810fb5a7536bbf732a7b07389a47b5`, is gated, and the configured
  `DineshAI` account can enumerate its 14 validation shards (6,693,093,726
  bytes).

These sources make a faithful reconstruction plausible, but they do not
identify the authors' unpublished 12,500/37,500 split. A compute-calibrated
full reconstruction is therefore a separate route rather than evidence from
this release audit.
