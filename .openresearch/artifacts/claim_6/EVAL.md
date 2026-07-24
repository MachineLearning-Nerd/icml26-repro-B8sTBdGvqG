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
