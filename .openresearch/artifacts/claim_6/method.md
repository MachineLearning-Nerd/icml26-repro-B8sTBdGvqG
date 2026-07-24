# Claim 6 method

## Route 1 — release and data-identity audit

The first route inspects the complete official Git tree, arXiv source package,
vendored runner, and current public dataset inventories. The executable audit:

1. enumerates every required severity-5 entropy file;
2. confirms that neither the vendored release nor its complete remote tree
   contains any required array or raw Figure 4 result;
3. statically reconstructs the CLI schema and `ExperimentConfig` fields;
4. runs the paper's documented command as a negative control and requires the
   released `args.gamma` defect to fail before data loading;
5. independently repeats the AST/file audit without importing author code.

This route can establish whether the released evidence is reproducible. It
cannot verify or falsify the numerical ImageNet-C claim.

## Route 2 — pinned source-figure digitization

The second route downloads the pinned arXiv source archive with an explicit
User-Agent, requires the archive and both Figure 4 PNG hashes to match, and
extracts exact-color curve and marker pixels. It checks three non-circular
properties:

1. conditional CTM crosses five fixed power levels earlier than standard CTM
   for each of `n=500` and `n=4000`;
2. the conditional crossing moves earlier from `n=100` to `500` to `4000`
   at four fixed power levels;
3. all six Blur/Weather ratio markers at `n=500,1000,4000` lie above one.

An independent checker reconstructs both axis transforms from raw CSV columns
without importing the digitizer or author code. Reversing method labels and
inverting the log-y calibration are required to contradict the result. This
route verifies what the pinned published figure encodes, not whether its raw
benchmark data regenerate, so its Claim 6 verdict remains `BLOCKED`.

## Planned distinct routes

- Route 3 begins with a CPU calibration over 192 images selected independently
  of the claim formula. It sweeps 1/8/16 preprocessing workers and all
  combinations of 8/16/32/64 inference threads with batch sizes 8/16/32,
  using three hash-verified Parquet files and the hash-verified default
  `timm` checkpoint. An independent checker recomputes the best setting and
  full 575,000-image projection. Only then will the full benchmark be run.
- The full Route 3 reconstruction will use a fixed, claim-independent
  12,500/37,500 partition of aligned clean/corrupted validation indexes,
  all 15 severity-5 corruptions, 10 seeds, and reference sizes at and above
  500. It will use the source-equivalent optimized CTM recurrences already
  regression-tested against the released implementation.
- Route 4, required if confidence remains LOW: seek an assumption-matched
  falsification using the complete reconstructed benchmark; missing data,
  runner crashes, and reduced subsets are explicitly ineligible.
