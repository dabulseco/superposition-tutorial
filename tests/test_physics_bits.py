"""Checks for Topic 1 physics (physics/bits.py), from spec section 6.1."""

from physics import bits


def test_classical_bit_always_reads_the_set_state():
    for state in ("ON", "OFF"):
        assert all(bits.measure_classical(state) == state for _ in range(1000))


def test_coin_slaps_are_fair_within_four_standard_errors():
    # 10,000 slaps: standard error is sqrt(10000 * 0.5 * 0.5) = 50 heads.
    inside = sum(abs(bits.slap_coins(10_000, seed)[0] - 5_000) <= 200
                 for seed in range(1000))
    assert inside >= 999


def test_heads_and_tails_add_up():
    heads, tails = bits.slap_coins(100, seed=3)
    assert heads + tails == 100


def test_same_seed_gives_same_result():
    assert bits.slap_coins(100, seed=5) == bits.slap_coins(100, seed=5)


def test_different_seeds_can_differ():
    assert len({bits.slap_coins(100, seed)[0] for seed in range(20)}) > 1


def test_zero_coins_gives_zero_counts():
    assert bits.slap_coins(0, seed=1) == (0, 0)


def test_biased_coin_follows_p_heads():
    assert bits.slap_coins(50, seed=1, p_heads=1.0) == (50, 0)
    assert bits.slap_coins(50, seed=1, p_heads=0.0) == (0, 50)
