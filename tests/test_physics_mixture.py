"""Checks for the superposition-vs-mixture physics (physics/mixture.py)."""

import numpy as np

from physics import mixture as mx

Z = mx.unit_vector(0, 0)
X = mx.unit_vector(90, 0)


def test_superposition_is_5050_along_z_and_certain_along_x():
    r = mx.bloch_vector_pure(90, 0)
    assert mx.probability_plus(r, Z) == 0.5 or abs(mx.probability_plus(r, Z) - 0.5) < 1e-12
    assert abs(mx.probability_plus(r, X) - 1.0) < 1e-12


def test_mixture_is_5050_along_z_and_along_x():
    r = mx.bloch_vector_mixture(90)
    assert abs(mx.probability_plus(r, Z) - 0.5) < 1e-12
    assert abs(mx.probability_plus(r, X) - 0.5) < 1e-12


def test_mixture_has_no_x_or_y_component():
    for theta in (0, 30, 90, 140, 180):
        r = mx.bloch_vector_mixture(theta)
        assert r[0] == 0 and r[1] == 0


def test_mixture_density_matrix_has_no_coherences():
    rho = mx.density_matrix(mx.bloch_vector_mixture(60))
    assert rho[0, 1] == 0 and rho[1, 0] == 0


def test_superposition_density_matrix_has_coherences():
    rho = mx.density_matrix(mx.bloch_vector_pure(90, 0))
    assert abs(rho[0, 1] - 0.5) < 1e-12


def test_simulate_shots_repeats_for_the_same_seed():
    assert mx.simulate_shots(0.3, 1000, 7) == mx.simulate_shots(0.3, 1000, 7)


def test_simulate_shots_never_exceeds_shot_count():
    assert 0 <= mx.simulate_shots(0.5, 10, 1) <= 10
    assert mx.simulate_shots(1.0, 10, 1) == 10
