# Claim 2 method

The witness selects the point-mass null \(P=\delta_0\). Both the reference set
and online stream are therefore iid from exactly the same null distribution
and deterministically equal zero.

Two paths are evaluated:

1. The exact Equation 8 betting factor with a legal, predictable constant
   \(\eta_t=0.5\) and \(k=10^{-6}\).
2. The released `CondCTM` implementation with the paper's DKW correction and
   released ONS update (`D=0.5`, `C=0.1`, `smooth_param=1e-6`).

For the point mass, every ordinary ECDF transform equals one. The exact DKW
error is zero. Both paths are multiplied until the first crossing of
\(1/\alpha=20\), and every transition is written to `trajectory.csv`.

The independent checker imports no released code. It reconstructs Equation 8,
the DKW width, the ONS recurrence, both wealth paths, and the theorem's inner
and outer probabilities from the raw trajectory.

Controls:

- reversing the fixed betting direction to \(\eta=-0.5\) must not cross;
- replacing the ordinary PIT at the atom with independent randomized PIT
  values must remove deterministic rejection. This repair is evaluated over
  256 predeclared seeds and 1,000 steps per seed.

The verifier fails closed: any missing assumption audit, recurrence mismatch,
absent crossing, ineffective control, or non-contradictory probability causes
a nonzero exit.
