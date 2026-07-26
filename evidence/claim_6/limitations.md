# Claim 6 limitations and deviations

- The official entropy arrays and Figure 4 raw tables are absent.
- The author-specific clean/corrupted 12,500/37,500 index split is not
  identified in the paper or release.
- The configured account cannot read the gated official ImageNet validation
  shards. A full reconstruction must disclose use of a pinned ungated mirror.
- The release's sudden-shift CLI has a missing `--gamma` argument.
- Source-image digitization is evidence about the plotted report, not an
  independent benchmark reproduction.
- Public raw images permit reconstruction, but model inference over the full
  benchmark must first be calibrated on the authorized CPU backend.
- Until a faithful full-scope reconstruction finishes, Claim 6 remains
  `BLOCKED`; no subset, proxy, or missing-data failure is called a
  falsification.
Route 3 did not produce full-scope ImageNet-C numbers. Fifteen HF cpu-upgrade
component jobs were launched after a CPU calibration and smoke run, but all
stalled before the first clean-inference checkpoint. Their logs ended after
dataset/model download, with no traceback, OOM marker, clean checkpoint,
corruption checkpoint, raw CSV, or terminal summary.

Route 4 did not find a valid falsification. Missing official arrays, reduced
subsets, off-scope plotted points, and infrastructure stalls are not
assumption-matched counterexamples to the paper's ImageNet-C numerical claim.

Therefore Claim 6 remains BLOCKED. It should only move to VERIFIED or FALSIFIED
if a full-scope ImageNet-C entropy reconstruction or the authors' raw arrays
become available and pass independent re-aggregation plus negative controls.
