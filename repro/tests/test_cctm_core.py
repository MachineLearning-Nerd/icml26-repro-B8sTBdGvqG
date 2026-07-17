import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "repro" / "src"))
sys.path.insert(0, str(ROOT / "upstream"))

from cctm_core import dkw_band, normal_trial, run_conditional_ctm, run_standard_ctm
from cond_ctm import CondCTM
from conformal_test import ConformalTest
from utils import empirical_cdf


def test_dkw_band_matches_pinned_source():
    from utils import compute_dkw_band

    assert dkw_band(2_000, 0.1) == compute_dkw_band(2_000, 0.1)


def test_conditional_transitions_match_pinned_source():
    rng = np.random.RandomState(7)
    calibration = rng.normal(size=37)
    stream = rng.normal(size=91)
    source = CondCTM(0.1, calibration, D=0.5, C=0.1, smooth_param=1e-6)
    source_bets = [source.step(float(value))[0] for value in stream]
    source_wealth = np.minimum(np.cumprod(source_bets), 1e250)

    reproduced = run_conditional_ctm(calibration, stream)
    np.testing.assert_allclose(reproduced.p_values, [empirical_cdf(calibration)(x) for x in stream], rtol=0, atol=0)
    np.testing.assert_allclose(reproduced.wealth, source_wealth, rtol=1e-13, atol=1e-13)


def test_growing_reference_transitions_match_pinned_source():
    generator = np.random.RandomState(19)
    calibration = generator.normal(size=23)
    stream = generator.normal(size=71)
    rng_state = generator.get_state()

    original_global_state = np.random.get_state()
    try:
        np.random.set_state(rng_state)
        source = ConformalTest(alpha=0.05, D=0.5)
        source_crossing, source_wealth = source.test_exchangeability(
            np.concatenate((calibration, stream)), cal_set_size=len(calibration), C=0.1
        )
    finally:
        np.random.set_state(original_global_state)

    replay_rng = np.random.RandomState()
    replay_rng.set_state(rng_state)
    reproduced = run_standard_ctm(calibration, stream, rng=replay_rng)
    np.testing.assert_allclose(reproduced.p_values, np.asarray(source.p_values[len(calibration):]), rtol=0, atol=0)
    np.testing.assert_allclose(reproduced.wealth, source_wealth[len(calibration):], rtol=1e-13, atol=1e-13)
    expected_crossing = -1 if source_crossing == -1 else source_crossing - len(calibration)
    assert reproduced.first_crossing == expected_crossing


def test_warmup_transitions_match_pinned_source():
    generator = np.random.RandomState(29)
    calibration = generator.normal(size=31)
    stream = generator.normal(size=83)
    rng_state = generator.get_state()
    warmup = 9

    source_conditional = CondCTM(0.1, calibration, D=0.5, C=0.1, smooth_param=1e-6)
    for value in stream[:warmup]:
        source_conditional.optim.step(source_conditional.cal_ecdf(value), smooth_param=1e-6)
    source_bets = [source_conditional.step(value)[0] for value in stream[warmup:]]
    reproduced_conditional = run_conditional_ctm(calibration, stream, warmup=warmup)
    np.testing.assert_allclose(
        reproduced_conditional.wealth[warmup:], np.cumprod(source_bets), rtol=1e-13, atol=1e-13
    )

    original_global_state = np.random.get_state()
    try:
        np.random.set_state(rng_state)
        source_standard = ConformalTest(alpha=0.05, D=0.5)
        source_crossing, source_wealth = source_standard.test_exchangeability(
            np.concatenate((calibration, stream)),
            cal_set_size=len(calibration),
            C=0.1,
            warmup_samples=warmup,
        )
    finally:
        np.random.set_state(original_global_state)
    replay_rng = np.random.RandomState()
    replay_rng.set_state(rng_state)
    reproduced_standard = run_standard_ctm(calibration, stream, rng=replay_rng, warmup=warmup)
    np.testing.assert_allclose(
        reproduced_standard.wealth, source_wealth[len(calibration):], rtol=1e-13, atol=1e-13
    )
    expected_crossing = -1 if source_crossing == -1 else source_crossing - len(calibration)
    assert reproduced_standard.first_crossing == expected_crossing


def test_shift_has_earlier_conditional_crossing_in_source_primary_setting_prefix():
    crossings = []
    for seed in range(12):
        conditional, standard = normal_trial(
            seed, calibration_size=2_000, test_size=1_000, shift=1.0, include_standard=True
        )
        assert standard is not None
        crossings.append((conditional.first_crossing, standard.first_crossing))
    conditional_crossings = [a for a, _ in crossings if a >= 0]
    standard_crossings = [b for _, b in crossings if b >= 0]
    assert conditional_crossings and standard_crossings
    assert float(np.median(conditional_crossings)) < float(np.median(standard_crossings))
