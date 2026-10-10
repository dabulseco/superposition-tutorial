"""
physics/oscillators.py — Topic 2: two weights on springs
========================================================

THE SYSTEM
----------
    wall --k-- [weight 1] --k_c-- [weight 2] --k-- wall

Two equal weights of mass m. Each is tied to its wall by a spring of
stiffness k, and they are joined by a coupling spring of stiffness k_c.
x1 and x2 are how far each weight is from its rest position (positive =
to the right).

THE PHYSICS IN ONE PARAGRAPH
----------------------------
Newton's second law gives

    m x1'' = -k x1 - k_c (x1 - x2)
    m x2'' = -k x2 - k_c (x2 - x1)

This system has two "normal modes" (the page calls them Patterns):
  Pattern 1: both weights move together.  omega_1 = sqrt(k / m)
  Pattern 2: the weights move opposite.   omega_2 = sqrt((k + 2 k_c) / m)
ANY motion is a combination (superposition) of the two patterns.

With the defaults k = m = 1 and k_c = 2.625, omega_1 = 1.0 and
omega_2 = 2.5, the values used in the original primer.

Units are arbitrary but consistent: positions in the slider's units
(-80 to 80), time in units where omega_1 = 1.
"""

import numpy as np

DEFAULT_K = 1.0
DEFAULT_KC = 2.625
DEFAULT_M = 1.0


def normal_modes(k: float, k_c: float, m: float):
    """
    Find the two patterns from the springs and masses.

    Solves the eigenvalue problem  K v = m omega^2 v  for the stiffness
    matrix K = [[k + k_c, -k_c], [-k_c, k + k_c]].

    Returns (frequencies, mode_vectors):
      frequencies   [omega_1, omega_2] in radians per time unit, slow first
      mode_vectors  two unit vectors; mode_vectors[0] is Pattern 1
                    (1, 1)/sqrt(2), mode_vectors[1] is Pattern 2
                    (1, -1)/sqrt(2). The overall sign of each is arbitrary.
    """
    stiffness = np.array([[k + k_c, -k_c], [-k_c, k + k_c]], dtype=float)
    eigenvalues, eigenvectors = np.linalg.eigh(stiffness / m)   # sorted, low first
    return np.sqrt(eigenvalues), eigenvectors.T


def mode_amplitudes(x1_0: float, x2_0: float) -> tuple[float, float]:
    """
    How much of each pattern is started by releasing the weights from rest
    at positions x1_0 and x2_0.

        A1 = (x1_0 + x2_0) / 2      (Pattern 1, in step)
        A2 = (x1_0 - x2_0) / 2      (Pattern 2, opposite)

    Same units as the positions. Either can be negative; the size |A| is
    what the spectrum shows.
    """
    return (x1_0 + x2_0) / 2, (x1_0 - x2_0) / 2


def positions(t, x1_0: float, x2_0: float, k: float = DEFAULT_K,
              k_c: float = DEFAULT_KC, m: float = DEFAULT_M):
    """
    Positions of both weights at time(s) t after release from rest.

        x1(t) = A1 cos(omega_1 t) + A2 cos(omega_2 t)
        x2(t) = A1 cos(omega_1 t) - A2 cos(omega_2 t)

    t may be a number or an array. Returns (x1, x2).
    """
    (omega_1, omega_2), _ = normal_modes(k, k_c, m)
    a1, a2 = mode_amplitudes(x1_0, x2_0)
    t = np.asarray(t, dtype=float)
    in_step = a1 * np.cos(omega_1 * t)
    opposite = a2 * np.cos(omega_2 * t)
    return in_step + opposite, in_step - opposite


def sample_times(duration: float = 64 * np.pi, dt: float = 0.05) -> np.ndarray:
    """
    Evenly spaced times for recording the motion before a Fourier transform.
    A long recording (about 200 time units) is what lets the transform tell
    two nearby frequencies apart.
    """
    return np.arange(0.0, duration, dt)


def spectrum(trace, dt: float, pad: int = 8):
    """
    Fourier transform of a recorded motion: which frequencies it contains,
    and how strongly.

    trace : positions sampled every dt time units
    Returns (omega, amplitude). A pure oscillation A cos(omega_0 t) gives a
    peak of height |A| at omega = omega_0.

    Two standard steps make the peak heights trustworthy for any frequency:
      * a Hann window fades the recording in and out, so a frequency that
        doesn't fit a whole number of cycles doesn't smear across the plot;
      * zero-padding (`pad` times the length) samples the peak finely
        enough that we read its top, not its shoulder.
    """
    trace = np.asarray(trace, dtype=float)
    window = np.hanning(len(trace))
    transformed = np.fft.rfft(trace * window, n=pad * len(trace))
    omega = 2 * np.pi * np.fft.rfftfreq(pad * len(trace), dt)
    # Dividing by the window's sum (and doubling, for the one-sided
    # transform) turns the peak height into the oscillation's amplitude.
    amplitude = 2 * np.abs(transformed) / window.sum()
    return omega, amplitude


def peak_height(omega, amplitude, target: float, half_width: float = 0.1) -> float:
    """The tallest point of the spectrum within half_width of `target`."""
    near = np.abs(np.asarray(omega) - target) <= half_width
    return float(np.max(np.asarray(amplitude)[near]))


def random_start(seed: int) -> tuple[int, int]:
    """
    Random starting positions (whole numbers from -80 to 80) that always
    start BOTH patterns. |x1| = |x2| would start only one pattern (or none),
    so those draws are thrown away.
    """
    rng = np.random.default_rng(seed)
    while True:
        x1, x2 = (int(v) for v in rng.integers(-80, 81, size=2))
        if abs(x1) != abs(x2):
            return x1, x2
