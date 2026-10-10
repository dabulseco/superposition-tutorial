"""Checks for Topic 3 physics (physics/qubit.py), from spec section 6.3."""

import numpy as np
import pytest

from physics import qubit


def test_arrow_angle_at_the_three_landmarks():
    assert qubit.theta_from_probability(0.5) == pytest.approx(90.0)
    assert qubit.theta_from_probability(1.0) == pytest.approx(0.0)
    assert qubit.theta_from_probability(0.0) == pytest.approx(180.0)


def test_arrow_angle_inverts_the_probability_rule():
    # P(UP) = cos^2(theta / 2)
    for p in (0.1, 0.36, 0.7):
        theta = np.radians(qubit.theta_from_probability(p))
        assert np.cos(theta / 2) ** 2 == pytest.approx(p)


@pytest.mark.parametrize("p_up", [0.1, 0.5, 0.7])
def test_measured_fraction_is_within_four_standard_errors(p_up):
    n = 10_000
    ups, downs = qubit.measure(p_up, n, seed=11)
    standard_error = np.sqrt(n * p_up * (1 - p_up))
    assert abs(ups - n * p_up) <= 4 * standard_error
    assert ups + downs == n


def test_certain_states_give_no_randomness():
    assert qubit.measure(1.0, 100, seed=1) == (100, 0)
    assert qubit.measure(0.0, 100, seed=1) == (0, 100)


def test_measure_each_agrees_with_measure():
    each = qubit.measure_each(0.7, 100, seed=4)
    assert len(each) == 100
    assert qubit.measure(0.7, 100, seed=4) == (int(each.sum()), 100 - int(each.sum()))


def test_running_fraction_ends_at_the_overall_fraction():
    outcomes = [1, 0, 1, 1]
    assert list(qubit.running_fraction(outcomes)) == pytest.approx([1, 0.5, 2 / 3, 0.75])
    assert len(qubit.running_fraction([])) == 0
