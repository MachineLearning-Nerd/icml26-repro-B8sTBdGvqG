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

## Planned distinct routes

- Route 2: independently digitize the two pinned Figure 4 source images,
  including axis calibration and deliberately wrong color/axis controls. This
  checks what the published figure actually encodes, not whether the benchmark
  regenerates.
- Route 3: reconstruct clean and severity-5 entropy arrays from pinned public
  raw-image revisions and the pinned `timm` checkpoint, after a CPU throughput
  calibration unrelated to the claimed detection formula.
- Route 4, required if confidence remains LOW: seek an assumption-matched
  falsification using the complete reconstructed benchmark; missing data,
  runner crashes, and reduced subsets are explicitly ineligible.
