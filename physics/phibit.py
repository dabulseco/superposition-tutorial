"""
physics/phibit.py — Topic 4: sound-like waves on a chain (the "phi-bit")
=======================================================================

THE SYSTEM
----------
A chain of weights joined to their neighbors by springs, each also tied to
a wall by a side spring, shaken at one end. Waves can travel along it in
either direction.

THE TWO BASIC STATES
--------------------
    State 0: a wave traveling LEFT     cos(k x + omega t)
    State 1: a wave traveling RIGHT    cos(k x - omega t)

Any combination is a superposition:

    u(x, t) = a_L cos(k x + omega t) + a_R cos(k x - omega t + delta)

a_L and a_R are the two AMPLITUDES and delta is their relative phase,
exactly the ingredients of a qubit state. With delta = 0 this is the
formula used in the original primer.

Equal amplitudes give a STANDING WAVE: the sum factors into a fixed shape
times a single oscillation in time,

    u = 2 a cos(k x + delta/2) cos(omega t - delta/2)

so there are points (nodes) that never move. Changing delta slides the
nodes along the chain by delta / (2 k).

Positions x are measured in weight spacings (weight n sits at x = n).
Angles named *_deg are in degrees.
"""

import numpy as np

# The original primer fits 1.5 wavelengths along its 12 weights.
DEFAULT_K = 2 * np.pi / (12 / 1.5)

# Status wording from the original primer.
LABEL_NONE = "You turned off all waves!"
LABEL_STATE0 = "Pure State 0 (Only Left)"
LABEL_STATE1 = "Pure State 1 (Only Right)"
LABEL_STANDING = "50/50 Superposition! (Standing Wave)"
LABEL_UNEVEN = "Superposition! (Uneven Mix)"

# The "real chain" used by the Go deeper option: masses m, neighbor springs
# K, side springs k0, chosen so the allowed band runs from omega = 1 to
# about 4.1, inside the range of the page's frequency slider (0.5 to 4).
CHAIN_M = 1.0
CHAIN_K = 4.0
CHAIN_K0 = 1.0


def displacement(x, t: float, a_left: float, a_right: float,
                 delta_deg: float = 0.0, k: float = DEFAULT_K,
                 omega: float = 1.5):
    """
    How far the chain is displaced at position(s) x and time t.

        u = a_left cos(k x + omega t) + a_right cos(k x - omega t + delta)

    x may be a number or an array. The result has the units of the
    amplitudes.
    """
    x = np.asarray(x, dtype=float)
    delta = np.radians(delta_deg)
    return (a_left * np.cos(k * x + omega * t)
            + a_right * np.cos(k * x - omega * t + delta))


def classify(a_left: float, a_right: float) -> str:
    """Name the state the way the original primer's status box does."""
    if a_left == 0 and a_right == 0:
        return LABEL_NONE
    if a_right == 0:
        return LABEL_STATE0
    if a_left == 0:
        return LABEL_STATE1
    if a_left == a_right:
        return LABEL_STANDING
    return LABEL_UNEVEN


def share_of_state_1(a_left: float, a_right: float):
    """
    The fraction of the wave's power carried by the right-traveling wave:

        a_right^2 / (a_left^2 + a_right^2)

    This is the same formula as a qubit's probability of |1>. Returns None
    when there is no wave at all.
    """
    power = a_left ** 2 + a_right ** 2
    if power == 0:
        return None
    return a_right ** 2 / power


def bloch_from_amplitudes(a_left: float, a_right: float, delta_deg: float):
    """
    Where the phi-bit's state sits on the qubit's sphere: (theta_deg, phi_deg).

        theta = 2 arctan(a_right / a_left)     phi = delta

    0 deg = all State 0 (left wave), 180 deg = all State 1 (right wave).
    Returns None when there is no wave at all.
    """
    if a_left == 0 and a_right == 0:
        return None
    # arctan2 handles a_left = 0, where a plain division would fail.
    theta = 2 * np.degrees(np.arctan2(a_right, a_left))
    return float(theta), delta_deg


def node_positions(k: float, delta_deg: float, length: float) -> np.ndarray:
    """
    Where the still points of the standing wave are, for 0 <= x <= length.

    Nodes are where cos(k x + delta/2) = 0, that is
        k x + delta/2 = pi/2 + n pi     (n any whole number).
    """
    delta = np.radians(delta_deg)
    first = int(np.ceil((delta / 2 - np.pi / 2) / np.pi))
    last = int(np.floor((k * length + delta / 2 - np.pi / 2) / np.pi))
    n = np.arange(first, last + 1)
    return (np.pi / 2 + n * np.pi - delta / 2) / k


# -----------------------------------------------------------------------------
# The real chain: frequency sets wavelength
# -----------------------------------------------------------------------------

def chain_dispersion(q, m: float = CHAIN_M, spring: float = CHAIN_K,
                     side: float = CHAIN_K0, a: float = 1.0):
    """
    Frequency of a wave with wave number q on the chain:

        omega^2 = k0/m + (4 K / m) sin^2(q a / 2)

    m = mass of each weight, K = neighbor spring, k0 = side spring,
    a = spacing between weights.
    """
    return np.sqrt(side / m + 4 * spring / m * np.sin(np.asarray(q) * a / 2) ** 2)


def chain_band(m: float = CHAIN_M, spring: float = CHAIN_K,
               side: float = CHAIN_K0) -> tuple[float, float]:
    """
    The lowest and highest frequencies that can travel along the chain.
    Below the lowest, the side springs hold the weights too firmly for a
    wave to get going; it just dies away from the driver.
    """
    return float(np.sqrt(side / m)), float(np.sqrt(side / m + 4 * spring / m))


def chain_wavenumber(omega: float, m: float = CHAIN_M, spring: float = CHAIN_K,
                     side: float = CHAIN_K0, a: float = 1.0):
    """
    The wave number q that a driving frequency omega produces (the
    dispersion relation solved for q), or None if omega is outside the
    band and no wave can travel.
    """
    low, high = chain_band(m, spring, side)
    if omega < low or omega > high:
        return None
    inside = (omega ** 2 * m - side) / (4 * spring)
    return float(2 / a * np.arcsin(np.sqrt(np.clip(inside, 0.0, 1.0))))


def chain_modes(n: int, m: float = CHAIN_M, spring: float = CHAIN_K,
                side: float = CHAIN_K0) -> np.ndarray:
    """
    The n natural frequencies of a chain of n weights (free ends), found
    numerically from its stiffness matrix. Used to check the formula above.
    """
    stiffness = np.zeros((n, n))
    for i in range(n):
        stiffness[i, i] = side
        for j in (i - 1, i + 1):
            if 0 <= j < n:
                stiffness[i, i] += spring
                stiffness[i, j] = -spring
    return np.sqrt(np.clip(np.linalg.eigvalsh(stiffness / m), 0, None))
