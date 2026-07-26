# Claim 2 evaluator contract

Run the repository's single fixed command:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

The run must print `CLAIM2_VERDICT=FALSIFIED` only after both checkers exit
zero. Inspect `raw_results.json`, `trajectory.csv`, `negative_controls.json`,
`verifier_output.json`, and `independent_checker_output.json` in this
directory.

The verdict concerns Theorem 3.1 exactly as written, including its “any null
distribution” quantifier. It does not claim that a continuity-restricted or
randomized-PIT repair is invalid.
