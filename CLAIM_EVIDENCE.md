# Claim-to-evidence ledger

This ledger answers three questions for every paper claim: what was tested,
which code produced the result, and which independent artifact decides whether
the result is publishable. A result is not promoted beyond the scope of its
inputs.

## Shared protocol

The pinned paper is arXiv `2602.13848` v2. The official implementation is
`shaersh/cctm@a9feb795d9fa98cc1d0c075f8f08a5c510c7a844`. The clean-room core is
`code/repro/src/cctm_core.py`; `code/repro/reference_ctm.py` is a committed,
minimal mirror of the tested upstream recurrences, so a fresh clone does not
depend on an ignored private `upstream/` directory. The test suite checks DKW,
conditional transitions, growing-reference ranks, warm-up behavior, and the
primary detection prefix against that pinned recurrence.

The historical full runner was:

```bash
cd code
uv sync --frozen
bash scripts/run_reproduction.sh
```

Its durable outputs are copied into the root `evidence/` tree. The current
package verifies those outputs without pretending that unavailable ImageNet-C
arrays exist.

## Claim 1 — faster shift detection

**Verdict: `VERIFIED_SCOPED`.**

The paper's mechanism is that the proposed conditional CTM compares each test
score with a fixed reference ECDF, while the standard CTM grows its reference
with test-time observations. The producer runs the full released synthetic
protocol: 100 repetitions of the primary `N(0,1)` to `N(1,1)` shift with 2,000
calibration observations and a 1,000-step stream, plus the released bias,
delayed-shift, and drift suites.

Production path:

1. `code/repro/run_full_synthetic.py` generates
   `evidence/synthetic/full_synthetic_summary.json`.
2. The primary result is 100/100 detections for both methods, with median
   crossing 21 for conditional CTM and 31 for the growing-reference CTM.
3. All nine supporting bias/delay/drift settings have a lower conditional
   median delay.
4. The fixed-reference contamination control reports late conditional ECDF
   mean `0.7434` versus growing-reference p-value `0.5551`.
5. `code/repro/verify_full_synthetic.py` and
   `evidence/synthetic/independent_verification.json` independently re-derive
   the rates, medians, and controls.

This verifies the released synthetic scope. It does not include C6's
ImageNet-C benchmark.

## Claim 2 — Theorem 3.1 anytime validity

**Verdict: `FALSIFIED_AS_WRITTEN`.**

The theorem quantifies over any null distribution. The audit uses the Dirac
point mass at zero, a reference of 2,000 iid draws, a 64-step iid stream,
`alpha=0.05`, `delta=0.1`, and the theorem's DKW confidence band. The ECDF is
the true CDF on the realized reference, so the stated confidence event holds
exactly.

Production path:

1. `code/repro/run_claim2_counterexample.py` produces the displayed Equation 8
   trajectory, the released ONS trajectory, controls, and metadata.
2. The displayed process crosses `1/alpha=20` at step 9; the released process
   crosses at step 10.
3. The independent checker reconstructs the DKW value, every transition, both
   crossing times, and the deterministic outer-reference contradiction without
   importing released implementation code.
4. `verify_claim2_counterexample.py`, `independent_check_claim2.py`, and
   `verify_frozen_claim2.py` are the decision gates.

The result falsifies the theorem's printed any-distribution statement. It does
not claim that every continuity-restricted or otherwise repaired variant is
false. The finite synthetic null sweep remains empirical context and is not
used as a proof of a universal theorem.

## Claim 3 — Theorem 3.3 power and stopping time

**Verdict: `VERIFIED_PROOF_AUDIT`.**

The paper claims asymptotic power one under the fixed-alternative and positive
effective-signal assumptions, together with the stated
`Delta_0^-2 log(1/(alpha Delta_0)) + Delta_0^-2` order. The audit identifies
two errors in the printed proof route, then checks a corrected route rather than
silently treating the printed algebra as valid.

Production path:

1. `code/repro/verify_claim3_proof.py` writes
   `evidence/claim_3/proof_certificate.json`.
2. The certificate covers 11 obligations: ONS loss mapping, interior/boundary
   feasible benchmark, logarithmic growth, strong-law crossing, variance
   coupling, explicit burn-in, Bernstein tail summation, positive-k continuity,
   and detection of the printed proof errors.
3. The certificate passes 952 rational-grid checks and 25 non-vacuous burn-in
   checks.
4. `code/repro/independent_check_claim3.py` rechecks the certificate without
   importing SymPy or author code; the contract and frozen verifiers complete
   the gate.

This is a machine-checked proof audit built on a standard ONS regret theorem,
not a proof-assistant formalization of that external theorem. Hidden constants
remain conditional on the fixed reference set and confidence band.

## Claim 4 — DKW correction

**Verdict: `VERIFIED_SCOPED`.**

The corrected conditional CTM includes the finite-reference confidence band;
the negative control removes it and treats fixed-reference p-values as iid
uniform. In the released synthetic artifact, the no-DKW control rejects 88% at
zero reported calibration points, while the corrected method rejects 0% there.
The independent aggregation also verifies a maximum corrected type-I rate of
0.01 over the 11-point null grid at nominal level 0.05.

The producer, evidence artifact, and independent gate are the same C1 path:
`run_full_synthetic.py`, `evidence/synthetic/full_synthetic_summary.json`,
`verify_full_synthetic.py`, and `independent_verification.json`.

## Claim 5 — synthetic power, delay, and false alarms

**Verdict: `VERIFIED_SCOPED`.**

The source-style synthetic suites cover three bias values, three delayed-shift
settings, and three gradual-drift settings. Every setting has a lower
conditional median post-shift delay. The 11-point null grid stays at 0–1%
conditional rejection, and the independent aggregation confirms the complete
artifact mode is the released synthetic protocol rather than a reduced proxy.

The output is produced and independently checked by the same full synthetic
path described for C1 and C4. No ImageNet-C claim is inferred from these
synthetic results.

## Claim 6 — ImageNet-C Figure 4

**Verdict: `BLOCKED`.**

The paper's ImageNet-C protocol uses severity 5, all 15 corruption types,
entropy scores from `timm/vit_base_patch16_224`, clean and corrupted entropy
arrays, a 37,500-example stream, 10 realizations, warm-up 50, and reference
sizes 100, 500, and 4,000. The official release does not contain the 12,500
clean entropy array or the fifteen 37,500-example corruption arrays.

Four independent routes are preserved:

1. **Release/data audit:** `audit_claim6_release.py` and its independent checker
   confirm the 16 required arrays and raw result tables are absent and record
   the release's broken `--gamma` path.
2. **Source-figure audit:** `digitize_claim6_figure.py` extracts the plotted
   Figure 4 trends and `independent_check_claim6_figure.py` reconstructs the
   transforms. This verifies what the published plot encodes, not the hidden
   benchmark data, so it remains non-claiming.
3. **Full reconstruction attempt:** `record_claim6_full_run_stall.py` records
   fifteen component jobs that stalled before the first clean-inference
   checkpoint. No numerical benchmark result is promoted.
4. **Falsification search:** `run_claim6_falsification_route.py` rejects
   missing-data, subset, off-scope, and infrastructure observations as invalid
   counterexamples. It found no full-scope assumption-matched falsification.

`verify_claim6_blocked_routes.py` requires all four routes to pass and keeps the
final verdict `BLOCKED`. C6 can move only after raw arrays or a faithful
full-scope reconstruction is independently re-aggregated.

## Non-claims

- The historical `6/12` score and `10/12` projection are provenance, not a new
  score from this cleanup.
- No complete ImageNet-C reproduction is claimed.
- No author endorsement or correspondence is claimed.
- A passing finite simulation is not presented as proof of a universal or
  asymptotic theorem.
- Historical `orx/*` names inside immutable run logs describe the original
  execution context; they are not final live branch names.
