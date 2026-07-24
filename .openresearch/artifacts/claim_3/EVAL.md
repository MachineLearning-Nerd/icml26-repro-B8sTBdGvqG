# Claim 3 evaluator contract

Run the single inherited command:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

Claim 3 is `VERIFIED` only if:

- `proof_certificate.json` marks every corrected obligation true;
- `negative_controls.json` detects both printed-proof errors;
- `verifier_output.json` and `independent_checker_output.json` both pass;
- the cumulative Claim 1/2/4/5 checks also pass.

This is proof-level evidence. The earlier increasing-horizon simulation is
retained as **Historical rejected baseline** because it cannot verify an
asymptotic theorem or a stopping-time order.
