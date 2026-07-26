# Overview


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_0d6d7f032da6", "created_at": "2026-07-17T12:15:09+00:00", "title": "Reproduction scope"}
-->
This reproduction targets the two live claims for **Testing For Distribution Shifts with Conditional Conformal Test Martingales** (OpenReview `B8sTBdGvqG`, arXiv `2602.13848`).

The author repository is pinned at `shaersh/cctm@a9feb795d9fa98cc1d0c075f8f08a5c510c7a844`. The completed CPU execution covers every released **synthetic** notebook protocol: Figures 1, 2, 3, 5, and 6, all with the authors' 100 repetitions. It does not claim to reproduce ImageNet-C: the author-required precomputed entropy arrays are absent from the release and have no download path.

The clean-room runner is source-equivalent at the scalar-update level and has five direct comparisons against the pinned implementation, including randomized growing-reference ranks and warm-up behavior.
