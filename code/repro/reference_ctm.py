"""Small pinned-source reference used by the source-equivalence tests.

This file mirrors only the recurrences exercised by the tests from
``shaersh/cctm`` at the commit recorded in ``SOURCE_MANIFEST.md``. Producers
use ``src/cctm_core.py`` instead, so a test can compare two implementations.
"""

from __future__ import annotations

import numpy as np


def compute_dkw_band(n: int, alpha: float) -> float:
    return float(np.sqrt(np.log(2 / alpha) / (2 * n)))


def empirical_cdf(data):
    data_sorted = np.sort(data)
    n = len(data_sorted)

    def cdf_function(x):
        return np.sum(data_sorted <= x) / n

    return cdf_function


def betting_function(u_t, betting_param=1.0, interval_eps=0.0, smooth_param=0.0):
    if smooth_param > 0:
        return 1 + (1 / (0.5 + (1 + smooth_param) * interval_eps)) * (
            betting_param * (u_t - 0.5)
            - np.sqrt(betting_param**2 + smooth_param**2) * interval_eps
        )
    return 1 + (1 / (0.5 + interval_eps)) * betting_param * (
        u_t - 0.5 - np.sign(betting_param) * interval_eps
    )


class ONS:
    def __init__(self, ci_eps, D=0.5):
        self.D = D
        self.ci_eps = ci_eps
        self.etas = [0]
        self.a = 1

    def step(self, u_t, smooth_param=0.0):
        eta_t = self.etas[-1]
        if smooth_param > 0:
            v_t_dot_eta_t = (1 / (0.5 + (1 + smooth_param) * self.ci_eps)) * (
                eta_t * (u_t - 0.5)
                - np.sqrt(eta_t**2 + smooth_param**2) * self.ci_eps
            )
            dv_t = (1 / (0.5 + (1 + smooth_param) * self.ci_eps)) * (
                u_t - 0.5 - eta_t * self.ci_eps / np.sqrt(eta_t**2 + smooth_param**2)
            )
            z_t = dv_t / (1 + v_t_dot_eta_t)
        else:
            v_t = (1 / (0.5 + self.ci_eps)) * (
                u_t - 0.5 - np.sign(eta_t) * self.ci_eps
            )
            z_t = v_t / (1 + eta_t * v_t)
        self.a = self.a + z_t**2
        eta_new = eta_t + (2 / (2 - np.log(3))) * z_t / self.a
        if abs(eta_new) > self.D:
            eta_new = self.D * np.sign(eta_new)
        self.etas.append(eta_new)
        return eta_new


class CondCTM:
    def __init__(self, ci_delta, cal_samples, D=1.3, C=0, smooth_param=0.0):
        if len(cal_samples) == 0:
            raise ValueError("cal_samples must contain at least one sample")
        if ci_delta <= 0:
            raise ValueError("ci_delta must be positive")
        self.n = len(cal_samples)
        self.cal_ecdf = empirical_cdf(cal_samples)
        self.smooth_param = smooth_param
        self.interval_eps = 0 if ci_delta >= 1 else compute_dkw_band(self.n, ci_delta)
        self.bets = []
        self.p_values = []
        self.optim = ONS(self.interval_eps, D)
        self.C = C

    def step(self, test_sample):
        u_t = self.cal_ecdf(test_sample)
        self.p_values.append(u_t)
        eta_t = self.optim.etas[-1]
        if abs(eta_t) < self.C:
            eta_t = 0
        bet_res = betting_function(
            u_t, eta_t, self.interval_eps, smooth_param=self.smooth_param
        )
        self.bets.append(bet_res)
        eta_t = self.optim.step(u_t, smooth_param=self.smooth_param)
        return bet_res, eta_t


class ConformalTest:
    def __init__(self, alpha=0.05, D=1.0):
        if not 0 < alpha < 1:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.threshold = 1 / alpha
        self.D = D
        self.scores = None
        self.n_scores = 0
        self.p_values = []

    def calculate_conformity_score(self, sample):
        return sample

    def _calculate_p_value(self, new_score):
        if self.n_scores > 0:
            scores_view = self.scores[: self.n_scores]
            smaller_count = np.sum(scores_view < new_score)
            equal_count = np.sum(scores_view == new_score)
        else:
            smaller_count = 0
            equal_count = 0
        equal_count += 1
        n = self.n_scores + 1
        return (np.random.uniform(0, 1) * equal_count + smaller_count) / n

    def test_exchangeability(
        self,
        test_set,
        cal_set_size=0,
        C=0.0,
        warmup_samples=0,
        calibration_size=None,
        warmup=None,
    ):
        if calibration_size is not None:
            cal_set_size = calibration_size
        if warmup is not None:
            warmup_samples = warmup
        test_set = np.array(test_set)
        self.scores = np.zeros(len(test_set), dtype=np.float64)
        self.n_scores = 0
        self.p_values = []
        for sample in test_set[:cal_set_size]:
            new_score = self.calculate_conformity_score(sample)
            p_value = self._calculate_p_value(new_score)
            self.p_values.append(p_value)
            self.scores[self.n_scores] = new_score
            self.n_scores += 1

        optim = ONS(ci_eps=0, D=self.D)
        current_martingale = 1.0
        martingale_values = [current_martingale] * cal_set_size
        first_exceeding_index = -1
        for idx, sample in enumerate(test_set[cal_set_size:]):
            new_score = self.calculate_conformity_score(sample)
            p_value = self._calculate_p_value(new_score)
            self.p_values.append(p_value)
            self.scores[self.n_scores] = new_score
            self.n_scores += 1
            if idx < warmup_samples:
                optim.step(p_value)
                martingale_values.append(1.0)
                continue
            eta_t = optim.etas[-1]
            if abs(eta_t) < C:
                eta_t = 0
            current_martingale *= 1 + eta_t * (p_value - 0.5)
            current_martingale = min(current_martingale, 1e250)
            optim.step(p_value)
            martingale_values.append(current_martingale)
            if current_martingale >= self.threshold and first_exceeding_index == -1:
                first_exceeding_index = len(martingale_values) - 1
        return first_exceeding_index, np.array(martingale_values)
