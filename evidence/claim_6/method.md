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

## Route 3 — full reconstruction attempt, stalled before evidence

The third route attempted to reconstruct clean and severity-5 entropy arrays
from pinned public raw-image revisions and the pinned `timm` checkpoint, after a
CPU throughput calibration unrelated to the claimed detection formula. The work
was split into 15 component runs, one for each ImageNet-C corruption.

All 15 component jobs remained marked running after roughly 26 hours, exceeded
the intended 16-hour Hugging Face timeout, and their logs stopped before the
first clean-inference checkpoint. Cancel requests were submitted. This route
therefore produced no eligible ImageNet-C numerical evidence and remains
`BLOCKED`.

## Route 4 — mandatory falsification search

The fourth route seeks a valid counterexample under the exact full-scope
ImageNet-C assumptions. It explicitly rejects invalid counterexamples:

1. missing official entropy arrays block regeneration but do not contradict the
   claim;
2. reduced smoke subsets are not full-scope ImageNet-C evidence;
3. a Digital-group plotted ratio below one at `n=100` is outside the audited
   Blur/Weather, `n>=500` ratio clause;
4. stalled infrastructure is not a numerical counterexample.

No assumption-matched full-scope counterexample is available, so the route also
ends in `BLOCKED`.
