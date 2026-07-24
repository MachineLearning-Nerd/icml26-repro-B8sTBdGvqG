# Claim 3 source audit

Source: ar5iv HTML for arXiv 2602.13848, retrieved 2026-07-24 with an
explicit browser User-Agent. SHA-256:
`ef9032cb84ff680f5b31cd19e67b2991839e669f7ce0f8d2cbaabd1120d273a3`.

The relevant anchors are Equation 11 (`S3.E11`), Equation 12 (`S3.E12`),
Lemma 3.2 (`S3.Thmtheorem2`), Theorem 3.3 (`S3.Thmtheorem3`), the ONS regret
lemma (`A4.Thmtheorem1`), and the theorem proof (`A5.SS5`).

## Exact assumptions and quantifiers

Conditional on a given fixed reference set \(D_0\):

- \(X_t\) are iid from one fixed alternative \(Q\ne P\) for all \(t\ge1\);
- \(k>0\) is sufficiently small;
- \(\Delta_k=|E[\widehat p_t-1/2\mid D_0]|
  -\sqrt{1+k^2}\,\bar\epsilon>0\);
- Algorithm 1 uses Algorithm 2's ONS bets in \([-1/2,1/2]\).

The theorem claims almost-sure finite stopping. In the limit \(k\to0\), it
also claims the displayed big-O expected-stopping-time order in \(\Delta_0\)
and \(\alpha\).

## Printed-proof defects

The proof's conclusion is not accepted verbatim:

1. Equations 63–68 use an unconstrained quadratic maximizer and state equality
   even when that maximizer lies outside \([-1/2,1/2]\).
2. Equation 73 has exponent
   \(-t\omega/32+(4/3)\log 3\), but the next paragraph defines a positive
   \(\lambda=\omega/32+(4/3)\log3\) and replaces the summand by
   \(e^{-\lambda t}\). These are not equal.

Both errors are explicit negative controls in the verifier. The corrected
derivation uses a feasible case-split benchmark and derives a fresh Bernstein
tail; it does not silently repair the displayed equations.

## Primary theorem used

The only imported mathematical component is the standard logarithmic regret
guarantee for Online Newton Step on exp-concave losses, cited by the paper to
Hazan, Agarwal, and Kale, *Logarithmic Regret Algorithms for Online Convex
Optimization* (Machine Learning 69, 2007, DOI 10.1007/s10994-007-5016-8).
The certificate separately checks the paper-specific domain, gradient, bet,
and regret-to-wealth mapping.
