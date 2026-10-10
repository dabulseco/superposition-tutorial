"""
physics/mixture.py — superposition vs. classical mixture for a spin-1/2
========================================================================

Any spin-1/2 (two-level) state can be described by a "Bloch vector" r.
  * A pure state (including any superposition) lies ON the sphere, |r| = 1.
  * A classical mixture lies INSIDE the sphere, |r| < 1.
Measured along a unit axis n, the probability of getting "+" is

        P(+) = (1 + r . n) / 2

Everything in this file is plain physics: no Streamlit and no language
model, so the functions can be tested on their own or called by an agent.
Angles are in degrees.
"""

import numpy as np


def unit_vector(polar_deg: float, azimuth_deg: float) -> np.ndarray:
    """
    Turn two angles into a 3D unit vector (x, y, z).

    polar_deg   : angle down from the +z axis (0 = straight up, 180 = down)
    azimuth_deg : angle around the z-axis, measured from +x toward +y
    """
    theta = np.radians(polar_deg)
    phi = np.radians(azimuth_deg)
    return np.array([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta),
    ])


def bloch_vector_pure(theta_deg: float, phi_deg: float) -> np.ndarray:
    """
    Bloch vector of the PURE superposition state

        |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>

    The vector sits on the surface of the sphere (length 1).
    theta sets the balance between |0> and |1>; phi is the relative phase.
    """
    return unit_vector(theta_deg, phi_deg)


def bloch_vector_mixture(theta_deg: float) -> np.ndarray:
    """
    Bloch vector of the CLASSICAL MIXTURE that has the same z-statistics:

        "|0> with probability cos^2(theta/2),
         |1> with probability sin^2(theta/2)"

    A mixture has no phase relationship between |0> and |1>, so its
    x and y components are zero. Only the z component survives.
    """
    p0 = np.cos(np.radians(theta_deg) / 2) ** 2
    p1 = 1 - p0
    return np.array([0.0, 0.0, p0 - p1])   # z = P(0) - P(1)


def density_matrix(r: np.ndarray) -> np.ndarray:
    """
    Convert a Bloch vector into the 2x2 density matrix

        rho = (I + rx*X + ry*Y + rz*Z) / 2

    The OFF-DIAGONAL entries are the "coherences". They are nonzero for a
    superposition and exactly zero for the mixture. They are what makes
    interference possible.
    """
    rx, ry, rz = r
    return 0.5 * np.array([
        [1 + rz,        rx - 1j * ry],
        [rx + 1j * ry,  1 - rz],
    ])


def probability_plus(r: np.ndarray, n: np.ndarray) -> float:
    """Born rule for spin-1/2: probability of '+' along axis n is (1 + r.n)/2."""
    p = 0.5 * (1 + float(np.dot(r, n)))
    return float(np.clip(p, 0.0, 1.0))   # clip guards against rounding error


def simulate_shots(p_plus: float, n_shots: int, seed: int) -> int:
    """
    Simulate n_shots individual measurements. Each shot is random; only the
    statistics are predictable. Returns how many shots came out '+'.
    """
    rng = np.random.default_rng(seed)
    return int(rng.binomial(n_shots, p_plus))


def describe_state(theta_deg: float, phi_deg: float) -> str:
    """Write the pure state in Dirac notation, for display."""
    a = np.cos(np.radians(theta_deg) / 2)
    b = np.sin(np.radians(theta_deg) / 2)
    return (rf"|\psi\rangle = {a:.3f}\,|0\rangle + "
            rf"e^{{i\,{phi_deg:.0f}^\circ}}\,{b:.3f}\,|1\rangle")
