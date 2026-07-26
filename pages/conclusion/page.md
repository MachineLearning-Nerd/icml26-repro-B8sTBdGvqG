# Conclusion


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_5b152c787318", "created_at": "2026-07-17T12:16:37+00:00", "title": "Executive summary", "pinned": true, "pinned_at": "2026-07-17T12:17:00+00:00"}
-->
**Both live claims are empirically reproduced at the full released synthetic scope.** Conditional CTM detected all 100 primary mean-shift streams at median 21 observations versus 31 for the growing-reference CTM, and it was faster in all nine released bias/delay/drift settings. Across the complete 11-setting, 20,000-step null grid it produced 0–1% false positives at nominal 5%; the no-DKW negative control reached 88%. Five direct source-equivalence tests and a separate raw-artifact verifier pass. The ImageNet-C data-dependent component is explicitly unexecuted because the source release omits its required entropy arrays.


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_32f46da4d6f7", "created_at": "2026-07-17T12:16:45+00:00", "title": "Scope & cost"}
-->
| | This reproduction |
|---|---|
| Scope | Every released synthetic notebook configuration: Figures 1, 2, 3, 5, and 6; ImageNet-C excluded only because the release omits required entropy arrays |
| Hardware | 4 vCPU, CPU-only |
| Full run time | 5m24s |
| Cost | $0 |
| Outcome | C1 and C2 empirically reproduced; asymptotic theorem not claimed as simulation proof |
