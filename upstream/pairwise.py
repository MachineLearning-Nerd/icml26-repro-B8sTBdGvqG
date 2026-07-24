"""Pairwise betting martingale tests and simple sequence simulators."""

from typing import Tuple, Optional
import warnings
import numpy as np


class PairwiseBettingContinuous:
    """Test exchangeability with pairwise betting for continuous data.

    The betting score compares the likelihood of consecutive triples under an
    AR(1) alternative before and after swapping the last two observations.
    """

    def __init__(self, alpha: float = 0.05):
        """Initialize the pairwise betting test.

        Parameters
        ----------
        alpha : float, default=0.05
            Significance level. The rejection threshold is ``1 / alpha``.
        """
        if not 0 < alpha < 1:
            raise ValueError("alpha must be between 0 and 1")

        self.alpha = alpha
        self.threshold = 1 / alpha

    def _trivariate_normal_pdf(self, x: float, y: float, z: float, 
                              a: float, sigma: float, mu: float) -> float:
        """Compute the AR(1) joint density factor for three observations.
        """
        if sigma <= 0:
            raise ValueError("sigma must be positive")

        # For AR(1): X_t+1 = a*X_t + ε_t+1
        # The conditional densities give us the joint density
        var = sigma**2

        # f(x,y,z) ∝ exp(-1/(2σ²) * [(y-ax)² + (z-ay)²])
        exponent = -0.5 * ((y - a*x - mu)**2 + (z - a*y - mu)**2) / var
        normalizer = 1 / (2 * np.pi * var)

        return normalizer * np.exp(exponent)

    def _estimate_parameters(self, data: np.ndarray, t: int) -> Tuple[float, float, float]:
        """Estimate AR(1) parameters from observations before time ``t``.

        Parameters
        ----------
        data : np.ndarray
            Observed sequence.
        t : int
            Current index; only ``data[:t-1]`` is used for estimation.

        Returns
        -------
        tuple[float, float, float]
            Estimates ``(a, sigma_squared, mu)``.
        """
        if t < 3:
            # Not enough data for estimation, return default values
            return 0.0, 1.0, 0.0

        # Use data up to t-1 for parameter estimation
        X = data[:t-1]

        if len(X) < 2:
            return 0.0, 1.0, 0.0

        # Least squares estimation: X_{i+1} = a * X_i + ε_{i+1}
        X_lag = X[:-1]  # X_1, ..., X_{t-2}
        X_lead = X[1:]  # X_2, ..., X_{t-1}

        # Avoid division by zero
        if np.sum(X_lag**2) == 0:
            a_hat = 0.0
        else:
            a_hat = np.sum(X_lag * X_lead) / np.sum(X_lag**2)

        # Estimate σ²
        if len(X_lead) > 1:
            residuals = X_lead - a_hat * X_lag
            sigma_sq_hat = np.sum(residuals**2) / (len(residuals) - 1)
            # Ensure positive variance
            sigma_sq_hat = max(sigma_sq_hat, 1e-6)
        else:
            sigma_sq_hat = 1.0

        # Estimate the mean
        if len(X_lead) > 1:
            mu_hat = np.mean(X_lead - a_hat * X_lag)
        else:
            mu_hat = 0.0

        return a_hat, sigma_sq_hat, mu_hat

    def _compute_betting_score(self, x_prev: float, x_curr: float, x_next: float,
                              a: float, sigma: float, mu: float) -> float:
        """Compute the pairwise betting score for one consecutive triple.

        Parameters
        ----------
        x_prev, x_curr, x_next : float
            Three consecutive observations.
        a, sigma, mu : float
            AR(1) coefficient, noise standard deviation, and drift.

        Returns
        -------
        float
            Likelihood-ratio betting score in ``[0, 2]`` when densities are
            finite and non-negative.
        """
        # Compute f(x_{t-1}, x_t, x_{t+1}) and f(x_{t-1}, x_{t+1}, x_t)
        f_ordered = self._trivariate_normal_pdf(x_prev, x_curr, x_next, a, sigma, mu)
        f_swapped = self._trivariate_normal_pdf(x_prev, x_next, x_curr, a, sigma, mu)

        # Avoid division by zero
        denominator = f_ordered + f_swapped
        if denominator == 0:
            return 1.0

        score = 2 * f_ordered / denominator
        return score
    def _compute_estimated_betting_score(self, x_prev: float, x_curr: float, x_next: float,
                                       a_hat: float, sigma_hat: float, mu_hat: float) -> float:
        """Compute the pairwise betting score with estimated AR(1) parameters."""
        return self._compute_betting_score(x_prev, x_curr, x_next, a_hat, sigma_hat, mu_hat)

    def test_exchangeability(self, data: np.ndarray, 
                           true_params: Optional[Tuple[float, float, float]] = None,
                           return_details: bool = False, cal_samples: int = 0) -> dict:
        """Run the pairwise betting test for exchangeability.

        Parameters
        ----------
        data : np.ndarray
            Sequence of observations.
        true_params : tuple[float, float, float], optional
            Oracle AR(1) parameters ``(a, sigma, mu)``. When omitted, parameters
            are estimated online from past observations.
        return_details : bool, default=False
            Include wealth, betting scores, estimated parameters, and sample
            count in the returned dictionary.
        cal_samples : int, default=0
            Number of initial observations to use before recording bets.

        Returns
        -------
        dict
            Test result containing rejection status, wealth summaries, stopping
            time, threshold, and significance level.
        """
        data = np.asarray(data, dtype=float)
        n = len(data)
        if n < 3:
            raise ValueError("Need at least 3 observations for the test")
        cal_samples = int(cal_samples)
        if cal_samples < 0:
            raise ValueError("cal_samples must be non-negative")
        if cal_samples > n:
            raise ValueError("cal_samples cannot exceed the number of observations")
        if true_params is not None:
            if len(true_params) != 3:
                raise ValueError("true_params must be a tuple of (a, sigma, mu)")
            if true_params[1] <= 0:
                raise ValueError("true_params sigma must be positive")

        # Initialize wealth
        W = [1.0, 1.0]  # W_0 = W_1 = 1 (we don't bet in first round)

        # Store betting scores for analysis
        betting_scores = []
        estimated_params = []

        # Perform betting from t=2 onwards (odd steps: t=3,5,7,...)
        for t in range(2, n):  # t goes from 2 to n-1
            if t % 2 == 1:  # Odd steps: t = 3, 5, 7, ...
                # We have observations X_{t-1}, X_t, X_{t+1}
                x_prev = data[t-1]
                x_curr = data[t]
                x_next = data[t+1] if t+1 < n else None

                if x_next is None:
                    break

                if true_params is not None:
                    # Oracle case with known parameters
                    a_true, sigma_true, mu_true = true_params
                    score = self._compute_betting_score(x_prev, x_curr, x_next, 
                                                      a_true, sigma_true, mu_true)
                else:
                    # Estimated case
                    a_hat, sigma_sq_hat, mu_hat = self._estimate_parameters(data, t)
                    sigma_hat = np.sqrt(sigma_sq_hat)
                    estimated_params.append((a_hat, sigma_hat, mu_hat))

                    score = self._compute_estimated_betting_score(x_prev, x_curr, x_next,
                                                                a_hat, sigma_hat, mu_hat)
                if t < cal_samples:
                    continue  # No betting during calibration phase
                betting_scores.append(score)

                # Update wealth: W_{t+1} = W_{t-1} × S_{t+1}
                if len(W) >= 2:
                    new_wealth = W[-2] * score  # W_{t-1} × S_{t+1}
                else:
                    new_wealth = score

                W.append(new_wealth)
            else:
                if t < cal_samples:
                    continue
                # Even steps: just copy previous wealth (no betting)
                W.append(W[-1])

        # Determine rejection
        max_wealth = max(W) if W else 1.0
        reject = max_wealth >= self.threshold

        # Find stopping time
        stopping_time = None
        for i, w in enumerate(W):
            if w >= self.threshold:
                stopping_time = i
                break

        results = {
            'reject_null': reject,
            'max_wealth': max_wealth,
            'final_wealth': W[-1] if W else 1.0,
            'stopping_time': stopping_time,
            'threshold': self.threshold,
            'alpha': self.alpha
        }

        if return_details:
            results.update({
                'wealth_sequence': W,
                'betting_scores': betting_scores,
                'estimated_params': estimated_params if true_params is None else None,
                'n_observations': n
            })

        return results

def simulate_ARm_process(n: int, a: float, sigma: float, mu: float = 0.,
                        x0: Optional[float] = None, m: int = 1) -> np.ndarray:
    """Simulate a scalar AR(1) process.

    Parameters
    ----------
    n : int
        Number of observations.
    a : float
        AR coefficient.
    sigma : float
        Noise standard deviation.
    mu : float, default=0.
        Noise mean/drift.
    x0 : float, optional
        Initial value. If omitted and ``abs(a) < 1``, it is drawn from the
        stationary distribution.
    m : int, default=1
        AR order. Only ``m=1`` is currently supported.

    Returns
    -------
    np.ndarray
        Simulated observations.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if m != 1:
        raise NotImplementedError("simulate_ARm_process currently supports only m=1")
    if abs(a) >= 1:
        warnings.warn("AR(m) process may not be stationary with |a| >= 1")

    # Initialize
    if x0 is None and abs(a) < 1:
        # Draw from stationary distribution
        stationary_var = sigma**2 / (1 - a**2)
        x0 = np.random.normal(0, np.sqrt(stationary_var))
    elif x0 is None:
        x0 = 0.0

    X = np.zeros(n)
    X[0] = x0

    # Generate process
    for t in range(m, n):
        epsilon = np.random.normal(mu, sigma)
        X[t] = epsilon
        for j in range(t-m,t):
            X[t] += a * X[j]
        # X[t] = a * X[t-1] + epsilon

    return X

def simulate_exchangeable_sequence(n: int, distribution: str = 'normal') -> np.ndarray:
    """Simulate an i.i.d. sequence, which is exchangeable.

    Parameters
    ----------
    n : int
        Number of observations.
    distribution : {"normal", "uniform", "exponential"}, default="normal"
        Marginal distribution to sample from.

    Returns
    -------
    np.ndarray
        Simulated observations.
    """
    if n <= 0:
        raise ValueError("n must be positive")

    if distribution == 'normal':
        return np.random.normal(0, 1, n)
    elif distribution == 'uniform':
        return np.random.uniform(-1, 1, n)
    elif distribution == 'exponential':
        return np.random.exponential(1, n)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
