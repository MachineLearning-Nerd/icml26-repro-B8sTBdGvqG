# Claim 6 evaluator contract

Run the inherited command:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

For Route 1, `release_audit.json`, `negative_control_output.json`, and
`independent_release_audit.json` must agree. The route verifier exits nonzero
if a required released array is found, the source hashes/protocol disagree, or
the documented CLI no longer fails for the audited missing-`gamma` reason.

Route 1's claim verdict is **BLOCKED**, not PASS: it establishes that the
official release cannot regenerate Figure 4. Claim 6 can become `VERIFIED` or
`FALSIFIED` only under the verdict rules in `claim_contract.json`.

For Route 2, inspect `route2_power_crossings.csv`,
`route2_ratio_points.csv`, `route2_figure_audit.json`,
`route2_negative_controls.json`, `route2_independent_checker.json`, and
`route2_verifier_output.json`. `route2_verifier_fail_closed.json` records a
subprocess test that removes one raw ratio row and requires the verifier to
exit nonzero. The verifier also exits nonzero on a source/image hash mismatch,
a missing curve/marker, a failed plotted comparison, a control that does not
expose the wrong interpretation, or an overclaim beyond `BLOCKED`.

For Route 3, inspect `route3_full_reconstruction_stall.json`. It records the 15
full component runs, their run IDs, log byte counts, and the absence of clean
or corruption inference checkpoints. This is a stalled full-reconstruction
attempt, not ImageNet-C claim evidence.

For Route 4, inspect `route4_falsification_attempt.json`. It is the mandatory
falsification route and must reject missing data, reduced smoke runs,
off-scope plotted points, and stalled infrastructure as invalid falsifications.

The final Claim 6 verifier is `final_blocked_verifier_output.json`. It requires
Routes 1-4 to be present, pass their own blocked-route checks, and agree that
Claim 6 remains **BLOCKED**.
