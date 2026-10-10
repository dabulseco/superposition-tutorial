"""Checks for Topic 4 physics (physics/phibit.py), from spec section 6.4."""

import warnings

import numpy as np
import pytest

from physics import phibit

X = np.arange(12.0)              # the twelve weights
K = phibit.DEFAULT_K
TIMES = [0.0, 0.37, 1.9, 4.4]


def test_zero_phase_reproduces_the_original_formula():
    for t in TIMES:
        ours = phibit.displacement(X, t, 0.8, 0.3, 0, K, 1.5)
        original = 0.8 * np.cos(K * X + 1.5 * t) + 0.3 * np.cos(K * X - 1.5 * t)
        assert np.allclose(ours, original, atol=1e-12)


def test_left_only_wave_travels_left():
    # A left-traveling wave keeps its shape while shifting toward -x:
    # u(x, t) = f(x + (omega/k) t).
    shift = 1.0 * K / 1.5        # time for the wave to move one weight
    now = phibit.displacement(X[1:], 0.0, 1, 0, 0, K, 1.5)
    later = phibit.displacement(X[:-1], shift, 1, 0, 0, K, 1.5)
    assert np.allclose(now, later, atol=1e-12)


@pytest.mark.parametrize("delta", [0, 40, 90, 215])
def test_equal_amplitudes_make_a_standing_wave(delta):
    d = np.radians(delta)
    for t in TIMES:
        ours = phibit.displacement(X, t, 0.6, 0.6, delta, K, 1.5)
        factored = 2 * 0.6 * np.cos(K * X + d / 2) * np.cos(1.5 * t - d / 2)
        assert np.allclose(ours, factored, atol=1e-12)


@pytest.mark.parametrize("delta", [0, 40, 90, 215])
def test_nodes_never_move_in_time(delta):
    nodes = phibit.node_positions(K, delta, length=11.0)
    assert len(nodes) >= 2
    assert np.all((nodes >= 0) & (nodes <= 11.0))
    for t in TIMES:
        still = phibit.displacement(nodes, t, 1, 1, delta, K, 1.5)
        assert np.allclose(still, 0, atol=1e-12)


def test_nodes_shift_by_delta_over_2k():
    # Use a long chain so the same nodes are in range before and after.
    before = phibit.node_positions(K, 0, length=40.0)
    after = phibit.node_positions(K, 60, length=40.0)
    shift = np.radians(60) / (2 * K)
    assert np.allclose(before[1:5] - shift, after[1:5], atol=1e-12) or \
        np.allclose(before[0:4] - shift, after[0:4], atol=1e-12)


def test_bloch_angles_and_share_for_a_3_4_5_state():
    theta, phi = phibit.bloch_from_amplitudes(0.8, 0.6, 0)
    assert theta == pytest.approx(73.74, abs=0.01)
    assert phi == 0
    assert phibit.share_of_state_1(0.8, 0.6) == pytest.approx(0.36)


def test_phase_becomes_the_angle_around_the_sphere():
    assert phibit.bloch_from_amplitudes(1, 1, 135) == (pytest.approx(90.0), 135)


def test_pure_states_sit_at_the_poles():
    assert phibit.bloch_from_amplitudes(1, 0, 0)[0] == pytest.approx(0.0)
    assert phibit.bloch_from_amplitudes(0, 1, 0)[0] == pytest.approx(180.0)
    assert phibit.share_of_state_1(1, 0) == 0.0
    assert phibit.share_of_state_1(0, 1) == 1.0


def test_classify_uses_the_original_five_labels():
    assert phibit.classify(100, 0) == "Pure State 0 (Only Left)"
    assert phibit.classify(0, 100) == "Pure State 1 (Only Right)"
    assert phibit.classify(100, 100) == "50/50 Superposition! (Standing Wave)"
    assert phibit.classify(35, 35) == "50/50 Superposition! (Standing Wave)"
    assert phibit.classify(100, 40) == "Superposition! (Uneven Mix)"
    assert phibit.classify(0, 0) == "You turned off all waves!"


def test_no_waves_gives_no_state_and_no_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert phibit.share_of_state_1(0, 0) is None
        assert phibit.bloch_from_amplitudes(0, 0, 0) is None
        assert np.all(phibit.displacement(X, 1.0, 0, 0, 0, K, 1.5) == 0)


# ---- the real chain (Go deeper) --------------------------------------------

M, SPRING, SIDE = phibit.CHAIN_M, phibit.CHAIN_K, phibit.CHAIN_K0


def test_chain_modes_fall_inside_the_allowed_band():
    modes = phibit.chain_modes(12, M, SPRING, SIDE)
    assert len(modes) == 12
    low, high = phibit.chain_band(M, SPRING, SIDE)
    assert low == pytest.approx(np.sqrt(SIDE / M))
    assert high == pytest.approx(np.sqrt(SIDE / M + 4 * SPRING / M))
    assert np.all(modes >= low - 1e-9) and np.all(modes <= high + 1e-9)


def test_dispersion_is_the_band_edges_at_its_extremes():
    low, high = phibit.chain_band(M, SPRING, SIDE)
    assert phibit.chain_dispersion(0.0, M, SPRING, SIDE) == pytest.approx(low)
    assert phibit.chain_dispersion(np.pi, M, SPRING, SIDE) == pytest.approx(high)


def test_wavenumber_inverts_the_dispersion_relation():
    for q in (0.3, 1.0, 2.5):
        omega = phibit.chain_dispersion(q, M, SPRING, SIDE)
        assert phibit.chain_wavenumber(omega, M, SPRING, SIDE) == pytest.approx(q)


def test_no_traveling_wave_outside_the_band():
    low, high = phibit.chain_band(M, SPRING, SIDE)
    assert phibit.chain_wavenumber(low - 0.1, M, SPRING, SIDE) is None
    assert phibit.chain_wavenumber(high + 0.1, M, SPRING, SIDE) is None
    assert phibit.chain_wavenumber(low, M, SPRING, SIDE) == pytest.approx(0.0)
