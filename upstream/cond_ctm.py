"""Conditional conformal test martingale with ONS-optimized betting."""

from optimization import ONS
from utils import betting_function, compute_dkw_band, empirical_cdf


class CondCTM:
    """Run an online exchangeability test from calibration samples.

    The class maps each test sample through the calibration empirical CDF,
    computes a confidence-adjusted betting score, and updates the betting
    parameter with an Online Newton Step optimizer.
    """

    def __init__(self, ci_delta, cal_samples, D=1.3, C=0, smooth_param=0.):
        """Initialize the conditional CTM state.

        Parameters
        ----------
        ci_delta : float
            DKW confidence level parameter. Values greater than or equal to 1
            disable the confidence-interval adjustment.
        cal_samples : array-like
            Calibration samples used to build the empirical CDF.
        D : float, default=1.3
            Absolute bound for the optimized betting parameter.
        C : float, default=0
            Threshold below which the current betting parameter is treated as 0
            when computing the next bet.
        smooth_param : float, default=0.
            Positive smoothing parameter passed to the betting function and ONS
            update.
        """
        if len(cal_samples) == 0:
            raise ValueError("cal_samples must contain at least one sample")
        if ci_delta <= 0:
            raise ValueError("ci_delta must be positive")

        self.n = len(cal_samples)
        self.ci_delta = ci_delta
        self.cal_ecdf = empirical_cdf(cal_samples)
        self.smooth_param = smooth_param

        if ci_delta >= 1:
            self.interval_eps = self.repr_eps = 0
        else:
            self.interval_eps = self.repr_eps = compute_dkw_band(self.n, ci_delta)

        self.bets = []
        self.p_values = []
        self.optim = ONS(self.interval_eps, D)

        self.C = C

    def step(self, test_sample):
        """Process one test sample and return its bet and updated eta.

        The returned bet can be multiplied into the running test martingale,
        while the returned eta is the optimizer state that will be used on the
        next step.
        """
        u_t = self.cal_ecdf(test_sample)

        self.p_values.append(u_t)

        eta_t = self.optim.etas[-1]
        if abs(eta_t) < self.C:
            eta_t = 0

        bet_res = betting_function(u_t, eta_t, self.interval_eps, smooth_param=self.smooth_param)
        self.bets.append(bet_res)

        eta_t = self.optim.step(
            u_t,
            smooth_param=self.smooth_param,
        )
        return bet_res, eta_t
