# Claim 3 corrected proof method

Let \(s=\operatorname{sign}E[\widehat p-1/2]\), let
\(Z=s(\widehat p-1/2)-\epsilon(\widehat p)\), and write
\(d=E[Z]=\Delta_0>0\). At \(k=0\), Equation 8 is
\(g=C_0 rZ\), where \(r=|\eta|\in[0,1/2]\) and
\(|Z|\le1/C_0\).

For \(g\in[-1/2,1/2]\), \(\log(1+g)\ge g-g^2\). Put
\(M_2=E[Z^2]\), and select

\[
q=C_0r=\min\{d/(2M_2), C_0/2\}.
\]

If the first term is feasible, the quadratic lower bound is
\(d^2/(4M_2)\). Otherwise the boundary choice gives
\(C_0d/2-C_0^2M_2/4>C_0d/4\). In either case it is at least
\(b=C_0^2d^2/4\), and the variance of \(g\) is at most the same
quadratic lower bound. Since log is 2-Lipschitz on the bet range,
the log-increment variance is at most four times its positive mean.

The standard ONS result gives pathwise regret
\(R_t\le2\log(1+4t)+1/2=o(t)\). The strong law applied to the fixed
benchmark then makes \(\log S_t\) grow linearly almost surely, proving finite
crossing.

For the mean stopping time, define

\[
t_0=\left\lceil {64\over\mu}
  \{\log(1/\alpha)+\log(64/\mu)+1\}\right\rceil ,
\]

where \(\mu\) is the benchmark's expected log increment. For every
\(t\ge t_0\), the no-crossing event implies a downward deviation of at least
\(t\mu/2\). Bernstein's inequality and the variance coupling yield
\(\Pr(\tau>t)\le\exp[-t\mu/B]\), with
\(B=32+(4/3)\log3\). Summing gives
\(E\tau\le t_0+B/\mu+1\). Since
\(\mu\ge C_0^2\Delta_0^2/4\), this is the claimed order for fixed confidence
band/reference set.

The \(k\to0\) statement follows by uniform continuity of Equation 8 for the
constructed nonzero benchmark: its positive mean and variance bound persist,
up to constants, for all sufficiently small positive \(k\). ONS itself is
therefore always applied at positive \(k\), where its derivative is defined.
