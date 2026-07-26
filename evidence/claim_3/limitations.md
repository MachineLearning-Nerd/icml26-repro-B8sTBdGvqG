# Claim 3 limitations and deviations

- The certificate reconstructs a corrected proof; it does not certify the
  erroneous algebra in Appendix E.5.
- It uses the published standard ONS regret theorem as a named lemma and
  machine-checks the mapping of this paper's loss into that lemma. It is not a
  proof-assistant formalization of the ONS theorem itself.
- The hidden big-O constant depends on the fixed reference set/confidence band
  through \(C_0^{-2}\). This is compatible with the theorem's conditional,
  fixed-\(D_0\) statement but should have been made explicit.
- The stopping-time order is a \(k\to0\) result. The continuity argument gives
  sufficiently small positive \(k\), not a claim for arbitrary smoothing.
- No finite sweep is presented as proof. The old horizon experiment is
  supporting context only.
