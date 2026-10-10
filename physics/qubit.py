"""
physics/qubit.py — Topic 3: measuring a qubit
=============================================

A qubit (here, an electron's spin) can be in a combination of UP |0> and
DOWN |1>:

        |psi> = cos(theta/2) |0> + sin(theta/2) |1>

Measuring it gives UP with probability P(UP) = cos^2(theta/2), otherwise
DOWN. Each single result is random; only the statistics are predictable.

This page keeps the relative phase at zero. The "Go deeper" page
(physics/mixture.py) adds it.
"""

import numpy as np


def theta_from_probability(p_up: float) -> float:
    """
    Tilt of the Bloch-sphere arrow, in degrees from straight up, for a
    qubit prepared with probability p_up of measuring UP.

        theta = 2 * arccos(sqrt(p_up))

    0 deg = certainly UP, 90 deg = 50/50, 180 deg = certainly DOWN.
    """
    return float(2 * np.degrees(np.arccos(np.sqrt(p_up))))


def measure_each(p_up: float, n: int, seed: int) -> np.ndarray:
    """
    Prepare and measure n qubits, one after another. Returns an array of
    n results: 1 for UP, 0 for DOWN. Each is UP with probability p_up.
    """
    rng = np.random.default_rng(seed)
    return (rng.random(n) < p_up).astype(int)


def measure(p_up: float, n: int, seed: int) -> tuple[int, int]:
    """Prepare and measure n qubits. Returns (ups, downs)."""
    ups = int(measure_each(p_up, n, seed).sum())
    return ups, n - ups


def running_fraction(outcomes) -> np.ndarray:
    """
    Fraction of UP results after each measurement so far (outcomes are 1
    for UP, 0 for DOWN). Shows how the measured fraction settles toward the
    set probability as the sample grows.
    """
    outcomes = np.asarray(outcomes, dtype=float)
    if outcomes.size == 0:
        return outcomes
    return np.cumsum(outcomes) / np.arange(1, outcomes.size + 1)
