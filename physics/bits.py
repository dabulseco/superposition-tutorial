"""
physics/bits.py — Topic 1: a classical bit and a spinning coin
==============================================================

A classical bit (a light switch) is always in one definite state, so
measuring it just reports that state. A spinning coin slapped down gives
heads or tails at random, 50/50.

No Streamlit and no language model here: just the rules.
"""

import numpy as np


def measure_classical(state: str) -> str:
    """
    Measure a classical bit. It was already in a definite state, so the
    measurement returns that state every time and changes nothing.
    """
    return state


def slap_coins(n: int, seed: int, p_heads: float = 0.5) -> tuple[int, int]:
    """
    Slap down n spinning coins. Each lands heads with probability p_heads,
    independently of the others. Returns (heads, tails).

    The number of heads follows the binomial distribution, with mean
    n * p_heads and standard deviation sqrt(n * p_heads * (1 - p_heads)).
    """
    rng = np.random.default_rng(seed)
    heads = int(rng.binomial(n, p_heads))
    return heads, n - heads
