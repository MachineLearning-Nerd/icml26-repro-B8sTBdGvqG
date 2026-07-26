# Claim 2 limitations and deviations

- The counterexample uses a discrete null rather than the continuous Gaussian
  simulations in the paper. This is not a domain deviation because Theorem
  3.1 explicitly quantifies over any null distribution and states no
  continuity assumption.
- The released code's smoothing scale differs infinitesimally from the
  displayed Equation 8 scale. The evidence therefore evaluates both the
  displayed equation and the released code independently; both cross.
- Randomized PIT is a repair control, not the algorithm claimed in the paper.
- The finite horizon does not approximate an asymptotic event: it contains a
  concrete finite threshold crossing, which is sufficient for the theorem's
  “there exists \(t\)” event.
