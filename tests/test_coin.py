"""Checks for the animated coin on Topic 1 (components/coin.py)."""

from components import coin
from tests.test_pages import run_page


def coin_markup(at):
    """The coin's HTML as drawn on the page."""
    return " ".join(h.proto.body for h in at.get("html"))


def test_a_coin_with_no_result_is_spinning():
    html = coin.coin_html(None)
    assert 'class="primer-coin spinning"' in html
    assert "spinning" in html.split('aria-label="')[1].split('"')[0]


def test_a_measured_coin_lands_on_its_result_and_settles():
    heads, tails = coin.coin_html("HEADS"), coin.coin_html("TAILS")
    assert 'class="primer-coin landed heads"' in heads
    assert 'class="primer-coin landed tails"' in tails
    assert "primer-coin-settle-heads" in heads and "primer-coin-settle-tails" in tails
    assert "HEADS" in heads.split('aria-label="')[1].split('"')[0]


def test_paused_coin_does_not_spin_and_shows_no_face():
    html = coin.coin_html(None, paused=True)
    assert 'class="primer-coin spinning paused"' in html
    # A frozen spin would show H or T and look like a result; it shows "?".
    assert ".primer-coin.paused .face" in html and "primer-coin-unknown" in html


def test_coin_respects_reduced_motion_and_uses_no_script():
    html = coin.coin_html(None)
    assert "prefers-reduced-motion: reduce" in html
    assert "<script" not in html.lower()


def test_same_state_gives_identical_markup_so_the_wobble_does_not_replay():
    assert coin.coin_html("HEADS") == coin.coin_html("HEADS")


# ---- on the page ------------------------------------------------------------

def test_t1_coin_spins_then_lands_on_the_measured_face_then_spins_again():
    at = run_page("t1")
    assert 'primer-coin spinning"' in coin_markup(at)
    at.button(key="t1_coin_btn").click().run()
    face = at.session_state["t1_coin"].lower()
    assert f'primer-coin landed {face}"' in coin_markup(at)
    at.button(key="t1_coin_btn").click().run()
    assert 'primer-coin spinning"' in coin_markup(at)


def test_t1_pause_switch_stops_the_spin():
    at = run_page("t1")
    at.toggle(key="t1_pause").set_value(True).run()
    assert 'primer-coin spinning paused"' in coin_markup(at)
    assert "paused" in " ".join(c.value for c in at.caption).lower()
