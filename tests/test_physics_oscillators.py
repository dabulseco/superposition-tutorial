"""Checks for Topic 2 physics (physics/oscillators.py), from spec section 6.2."""

import numpy as np

from physics import oscillators as osc


def test_default_frequencies_match_the_original_primer():
    frequencies, _ = osc.normal_modes(1.0, 2.625, 1.0)
    assert abs(frequencies[0] - 1.0) < 1e-9
    assert abs(frequencies[1] - 2.5) < 1e-9


def test_mode_vectors_are_in_step_and_opposite():
    _, vectors = osc.normal_modes(1.0, 2.625, 1.0)
    s = 1 / np.sqrt(2)
    # A mode vector's overall sign is arbitrary, so compare up to sign.
    assert np.allclose(np.abs(vectors[0]), [s, s])
    assert vectors[0][0] * vectors[0][1] > 0          # same direction
    assert np.allclose(np.abs(vectors[1]), [s, s])
    assert vectors[1][0] * vectors[1][1] < 0          # opposite directions


def test_pattern_2_frequency_rises_with_coupling_but_pattern_1_does_not():
    weak, _ = osc.normal_modes(1.0, 1.0, 1.0)
    strong, _ = osc.normal_modes(1.0, 4.0, 1.0)
    assert abs(weak[0] - strong[0]) < 1e-12
    assert strong[1] > weak[1]


def test_mode_amplitudes_for_the_presets_and_a_one_sided_pull():
    assert osc.mode_amplitudes(40, 40) == (40, 0)       # Pattern 1 only
    assert osc.mode_amplitudes(40, -40) == (0, 40)      # Pattern 2 only
    assert osc.mode_amplitudes(40, 0) == (20, 20)       # equal amounts of both
    assert osc.mode_amplitudes(0, 0) == (0, 0)


def test_positions_start_where_the_weights_were_released():
    x1, x2 = osc.positions(np.array([0.0]), 40, -10)
    assert abs(x1[0] - 40) < 1e-12 and abs(x2[0] + 10) < 1e-12


def _newton_rk4(x1_0, x2_0, k, k_c, m, dt, steps):
    """Solve Newton's equations directly, step by step (Runge-Kutta 4)."""
    def rate(y):
        x1, x2, v1, v2 = y
        a1 = (-k * x1 - k_c * (x1 - x2)) / m
        a2 = (-k * x2 - k_c * (x2 - x1)) / m
        return np.array([v1, v2, a1, a2])

    y = np.array([x1_0, x2_0, 0.0, 0.0])
    out = [y[:2].copy()]
    for _ in range(steps):
        k1 = rate(y)
        k2 = rate(y + dt / 2 * k1)
        k3 = rate(y + dt / 2 * k2)
        k4 = rate(y + dt * k3)
        y = y + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out.append(y[:2].copy())
    return np.array(out)


def test_formula_matches_newtons_equations():
    dt, steps = 1e-3, 30_000          # 30 time units
    numeric = _newton_rk4(40, -10, 1.0, 2.625, 1.0, dt, steps)
    t = np.arange(steps + 1) * dt
    x1, x2 = osc.positions(t, 40, -10)
    assert np.max(np.abs(x1 - numeric[:, 0])) < 1e-6
    assert np.max(np.abs(x2 - numeric[:, 1])) < 1e-6


def test_spectrum_peaks_sit_at_the_mode_frequencies_with_the_mode_amplitudes():
    t = osc.sample_times()
    x1, _ = osc.positions(t, 40, -10)
    omega, amplitude = osc.spectrum(x1, t[1] - t[0])
    peak1 = osc.peak_height(omega, amplitude, 1.0)
    peak2 = osc.peak_height(omega, amplitude, 2.5)
    assert abs(peak1 - 15) < 0.15       # |A1| = 15, to 1%
    assert abs(peak2 - 25) < 0.25       # |A2| = 25, to 1%
    assert abs(omega[np.argmax(amplitude)] - 2.5) < 0.02


def test_spectrum_shows_one_peak_for_a_pure_pattern():
    t = osc.sample_times()
    x1, _ = osc.positions(t, 40, 40)
    omega, amplitude = osc.spectrum(x1, t[1] - t[0])
    assert abs(osc.peak_height(omega, amplitude, 1.0) - 40) < 0.4
    assert osc.peak_height(omega, amplitude, 2.5) < 0.4


def test_spectrum_still_measures_amplitudes_when_coupling_changes():
    frequencies, _ = osc.normal_modes(1.0, 1.3, 1.0)
    t = osc.sample_times()
    x1, _ = osc.positions(t, 60, 20, k_c=1.3)
    omega, amplitude = osc.spectrum(x1, t[1] - t[0])
    assert abs(osc.peak_height(omega, amplitude, frequencies[0]) - 40) < 0.4
    assert abs(osc.peak_height(omega, amplitude, frequencies[1]) - 20) < 0.4


def test_spectrum_of_no_motion_is_zero():
    t = osc.sample_times()
    omega, amplitude = osc.spectrum(np.zeros_like(t), t[1] - t[0])
    assert np.all(amplitude == 0)


def test_random_start_never_gives_a_pure_pattern():
    for seed in range(1000):
        x1, x2 = osc.random_start(seed)
        assert abs(x1) != abs(x2)
        assert -80 <= x1 <= 80 and -80 <= x2 <= 80
