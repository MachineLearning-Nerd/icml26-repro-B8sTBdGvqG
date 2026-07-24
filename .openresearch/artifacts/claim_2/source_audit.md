# Claim 2 source audit

Source: ar5iv HTML for arXiv 2602.13848, retrieved 2026-07-24 with an
explicit browser User-Agent. SHA-256:
`ef9032cb84ff680f5b31cd19e67b2991839e669f7ce0f8d2cbaabd1120d273a3`.

## Exact scope and quantifiers

The paragraph at `S3.SS1.p7` says the guarantee is finite-sample and holds for
any null distribution \(P\). Theorem 3.1 at `S3.Thmtheorem1` assumes:

- a fixed reference set \(D_0\) used to estimate the null ECDF;
- confidence bounds satisfying Equation 6 at a chosen
  \(\delta\in(0,1)\);
- any \(\alpha\in(0,1)\).

It concludes

\[
\Pr_{D_0}\{\Pr_{H_0}(\exists t\ge1:S_t\ge1/\alpha\mid
\mathcal F_{t-1},D_0)\le\alpha\}\ge1-\delta.
\]

No continuity, atomlessness, or randomized probability-integral-transform
assumption appears in the theorem.

## Proof obligation that fails

The proof at `A5.SS1.2.1.p1` sets
\(\mathbb E[F(X_t)-1/2\mid\mathcal F_{t-1},D_0]=0\) by the probability
integral transform. For a general CDF this is false in the presence of atoms.
For \(P=\delta_0\), \(F(X_t)=1\) almost surely and the expectation is \(1/2\),
not zero.

The counterexample does not rely on a bad ECDF estimate: when every reference
observation equals zero, \(\widehat F_0=F\) everywhere and the DKW error is
exactly zero.

## Interpretation

This audit tests the theorem as written. A corrected theorem restricted to
continuous nulls, or one using a randomized PIT at atoms, is a materially
different claim and is treated only as a negative control.
