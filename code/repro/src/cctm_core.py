"""Source-equivalent CPU implementation of the released CCTM recurrences.

The pinned author code implements the ECDF as a fresh linear scan and the
online rank as another linear scan.  That is transparent but makes the released
20,000-step, 1,100-trial null experiment needlessly expensive.  This module
keeps the scalar mathematical updates unchanged while using binary search for
the fixed ECDF and a Fenwick tree for growing-reference ranks.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class MartingaleRun:
    """Per-test-point p-values, wealth, and first Ville-threshold crossing."""

    p_values: np.ndarray
    wealth: np.ndarray
    first_crossing: int


class _Fenwick:
    """Integer prefix sums with zero-based public indexes."""

    def __init__(self, size: int) -> None:
        self._tree = np.zeros(size + 1, dtype=np.int64)

    def add(self, index: int, value: int = 1) -> None:
        i = index + 1
        while i < len(self._tree):
            self._tree[i] += value
            i += i & -i

    def prefix(self, stop: int) -> int:
        """Return the sum over the half-open interval [0, stop)."""
        total = 0
        i = stop
        while i:
            total += int(self._tree[i])
            i -= i & -i
        return total


def dkw_band(n: int, delta: float) -> float:
    """Match ``upstream.utils.compute_dkw_band`` exactly."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 < delta < 1.0:
        raise ValueError("delta must lie in (0, 1)")
    return sqrt(log(2.0 / delta) / (2.0 * n))


def _update_ons(eta: float, a: float, u: float, eps: float, D: float, smooth: float) -> tuple[float, float]:
    """One exact scalar transition from ``upstream.optimization.ONS.step``."""
    if smooth <= 0.0:
        v = (u - 0.5 - np.sign(eta) * eps) / (0.5 + eps)
        z = v / (1.0 + eta * v)
    else:
        root = sqrt(eta * eta + smooth * smooth)
        denominator = 0.5 + (1.0 + smooth) * eps
        v_dot_eta = (eta * (u - 0.5) - root * eps) / denominator
        derivative = (u - 0.5 - eta * eps / root) / denominator
        z = derivative / (1.0 + v_dot_eta)
    a_next = a + z * z
    eta_next = eta + (2.0 / (2.0 - log(3.0))) * z / a_next
    return float(np.clip(eta_next, -D, D)), float(a_next)


def _bet(u: float, eta: float, eps: float, smooth: float) -> float:
    """Match ``upstream.utils.betting_function`` for positive smoothing."""
    if smooth <= 0.0:
        return float(1.0 + eta * (u - 0.5 - np.sign(eta) * eps) / (0.5 + eps))
    return float(
        1.0
        + (eta * (u - 0.5) - sqrt(eta * eta + smooth * smooth) * eps)
        / (0.5 + (1.0 + smooth) * eps)
    )


def run_conditional_ctm(
    calibration: Iterable[float],
    stream: Iterable[float],
    *,
    ci_delta: float = 0.1,
    D: float = 0.5,
    clip_C: float = 0.1,
    smooth: float = 1e-6,
    warmup: int = 0,
    test_alpha: float = 0.05,
) -> MartingaleRun:
    """Run the fixed-reference CCTM, exactly preserving author recurrences."""
    calibration_array = np.asarray(list(calibration), dtype=np.float64)
    stream_array = np.asarray(list(stream), dtype=np.float64)
    if calibration_array.size == 0:
        raise ValueError("calibration must be non-empty")
    if not np.isfinite(calibration_array).all() or not np.isfinite(stream_array).all():
        raise ValueError("inputs must be finite")
    if not 0 <= warmup <= stream_array.size:
        raise ValueError("warmup must be within the stream")
    if D <= 0.0 or not 0.0 < test_alpha < 1.0:
        raise ValueError("invalid D or test_alpha")

    sorted_calibration = np.sort(calibration_array)
    eps = 0.0 if ci_delta >= 1.0 else dkw_band(sorted_calibration.size, ci_delta)
    p_values = np.searchsorted(sorted_calibration, stream_array, side="right") / sorted_calibration.size
    wealth = np.ones(stream_array.size, dtype=np.float64)
    eta, a, current = 0.0, 1.0, 1.0
    crossing = -1
    threshold = 1.0 / test_alpha

    for t, u in enumerate(p_values):
        if t >= warmup:
            eta_for_bet = 0.0 if abs(eta) < clip_C else eta
            bet = _bet(float(u), eta_for_bet, eps, smooth)
            if not bet > 0.0:
                raise ArithmeticError("non-positive betting factor")
            current = min(current * bet, 1e250)
            wealth[t] = current
            if crossing == -1 and current >= threshold:
                crossing = t
        eta, a = _update_ons(eta, a, float(u), eps, D, smooth)

    return MartingaleRun(p_values=p_values, wealth=wealth, first_crossing=crossing)


def run_standard_ctm(
    calibration: Iterable[float],
    stream: Iterable[float],
    *,
    rng: np.random.RandomState,
    D: float = 0.5,
    clip_C: float = 0.1,
    warmup: int = 0,
    test_alpha: float = 0.05,
) -> MartingaleRun:
    """Run the released growing-reference baseline with exact randomized ranks.

    ``rng`` must be at the same state that the author code has immediately
    before ``ConformalTest.test_exchangeability``.  This permits byte-level
    comparisons in tests while retaining O(log T) rank queries.
    """
    calibration_array = np.asarray(list(calibration), dtype=np.float64)
    stream_array = np.asarray(list(stream), dtype=np.float64)
    if calibration_array.size == 0:
        raise ValueError("calibration must be non-empty")
    if not 0 <= warmup <= stream_array.size:
        raise ValueError("warmup must be within the stream")

    all_values = np.concatenate((calibration_array, stream_array))
    coordinates = np.unique(all_values)
    tree = _Fenwick(coordinates.size)

    def randomized_rank(value: float, seen: int) -> float:
        index = int(np.searchsorted(coordinates, value, side="left"))
        smaller = tree.prefix(index)
        equal = tree.prefix(index + 1) - smaller
        p_value = (smaller + rng.uniform(0.0, 1.0) * (equal + 1)) / (seen + 1)
        tree.add(index)
        return float(p_value)

    seen = 0
    for value in calibration_array:
        randomized_rank(float(value), seen)
        seen += 1

    p_values = np.empty(stream_array.size, dtype=np.float64)
    wealth = np.ones(stream_array.size, dtype=np.float64)
    eta, a, current = 0.0, 1.0, 1.0
    crossing = -1
    threshold = 1.0 / test_alpha
    for t, value in enumerate(stream_array):
        p_value = randomized_rank(float(value), seen)
        seen += 1
        p_values[t] = p_value
        if t < warmup:
            eta, a = _update_ons(eta, a, p_value, 0.0, D, 0.0)
            continue
        eta_for_bet = 0.0 if abs(eta) < clip_C else eta
        bet = 1.0 + eta_for_bet * (p_value - 0.5)
        if not bet > 0.0:
            raise ArithmeticError("non-positive betting factor")
        current = min(current * bet, 1e250)
        wealth[t] = current
        if crossing == -1 and current >= threshold:
            crossing = t
        eta, a = _update_ons(eta, a, p_value, 0.0, D, 0.0)

    return MartingaleRun(p_values=p_values, wealth=wealth, first_crossing=crossing)


def normal_trial(
    seed: int,
    *,
    calibration_size: int,
    test_size: int,
    shift: float = 0.0,
    delay: int = 0,
    ci_delta: float = 0.1,
    warmup: int = 0,
    D: float = 0.5,
    clip_C: float = 0.1,
    smooth: float = 1e-6,
    test_alpha: float = 0.05,
    include_standard: bool = True,
) -> tuple[MartingaleRun, MartingaleRun | None]:
    """Author-compatible normal-stream generator used by the main protocol."""
    if not 0 <= delay <= test_size:
        raise ValueError("delay must lie within the test stream")
    rng = np.random.RandomState(seed)
    calibration = rng.normal(0.0, 1.0, calibration_size)
    stream = rng.normal(0.0, 1.0, test_size)
    stream[delay:] += shift
    conditional = run_conditional_ctm(
        calibration,
        stream,
        ci_delta=ci_delta,
        D=D,
        clip_C=clip_C,
        smooth=smooth,
        warmup=warmup,
        test_alpha=test_alpha,
    )
    standard = (
        run_standard_ctm(
            calibration,
            stream,
            rng=rng,
            D=D,
            clip_C=clip_C,
            warmup=warmup,
            test_alpha=test_alpha,
        )
        if include_standard
        else None
    )
    return conditional, standard
