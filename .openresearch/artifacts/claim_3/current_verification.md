# Claim 3 — current verification

**Verdict: VERIFIED.**

The current verifier is `repro/verify_claim3_contract.py`, supported by the
symbolic certificate in `repro/verify_claim3_proof.py` and the independently
implemented standard-library checker in `repro/independent_check_claim3.py`.
Run all three through the single inherited command:

```bash
uv sync --frozen && bash scripts/run_reproduction.sh
```

The accepted run is `dbf0c946-185a-485a-a114-08cda4561258` at Git SHA
`a693f6e7060b4241fb6defcb37229d3efbcf07ee`. It used Hugging Face
`cpu-upgrade`; 4 CPU cores were estimated, 64 were allocated, the whole
cumulative run took 6m59s, and the Claim 3 certificate took 3 seconds.

All 11 corrected proof obligations passed. The checker separately evaluated
952 exact rational benchmark cases and 25 burn-in cases. Both negative controls
detected genuine errors in the printed appendix proof: an infeasible
unconstrained optimizer and an inconsistent Equation 73 tail-rate
substitution. The corrected derivation establishes almost-sure crossing and
the stated expected-stopping order, conditional on a fixed reference set and
its fixed positive confidence-band scale.

## Historical rejected baseline

The earlier increasing-horizon simulation is retained as historical evidence,
but it is rejected as a theorem verifier. A finite simulation cannot establish
an asymptotic universal statement or the claimed stopping-time order.
