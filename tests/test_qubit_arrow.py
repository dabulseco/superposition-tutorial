"""Checks for the animated qubit arrow on Topic 3 (components/qubit_arrow.py)."""

import re

from components import qubit_arrow
from tests.test_pages import run_page


def arrow_markup(at):
    """The arrow's HTML as drawn on the page."""
    return " ".join(h.proto.body for h in at.get("html")
                    if "primer-qubit" in h.proto.body)


def label(html):
    return html.split('aria-label="')[1].split('"')[0]


def angle(html, name):
    """One of the angles handed to the drawing, in degrees."""
    return float(re.search(rf"--{name}: (-?[\d.]+)deg", html).group(1))


def test_prepared_arrow_rests_at_its_tilt_without_moving():
    html = qubit_arrow.arrow_html(60)
    assert 'class="primer-qubit-arrow prepared"' in html
    assert angle(html, "to") == 60
    assert "60" in label(html)


def test_measured_up_swings_from_the_prepared_tilt_to_the_top():
    html = qubit_arrow.arrow_html(60, "UP")
    assert 'class="primer-qubit-arrow snapped"' in html
    assert angle(html, "from") == 60 and angle(html, "to") == 0
    assert "UP" in label(html)


def test_measured_down_swings_to_the_bottom():
    html = qubit_arrow.arrow_html(60, "DOWN")
    assert angle(html, "from") == 60 and angle(html, "to") == 180


def test_swing_overshoots_the_pole_then_comes_back():
    html = qubit_arrow.arrow_html(60, "UP")
    assert angle(html, "over") < 0          # past the top, then back
    html = qubit_arrow.arrow_html(60, "DOWN")
    assert angle(html, "over") > 180        # past the bottom, then back


def test_arrow_already_at_the_pole_does_not_move():
    html = qubit_arrow.arrow_html(0, "UP")
    assert angle(html, "from") == angle(html, "over") == angle(html, "to") == 0


def test_a_new_measurement_changes_the_markup_so_the_swing_replays():
    # Two UP results in a row must still look like two measurements.
    assert (qubit_arrow.arrow_html(60, "UP", shot=1)
            != qubit_arrow.arrow_html(60, "UP", shot=2))
    assert (qubit_arrow.arrow_html(60, "UP", shot=1)
            == qubit_arrow.arrow_html(60, "UP", shot=1))


def test_arrow_respects_reduced_motion_and_uses_no_script():
    html = qubit_arrow.arrow_html(60, "UP")
    assert "prefers-reduced-motion: reduce" in html
    assert "<script" not in html.lower()


# ---- on the page ------------------------------------------------------------

def test_t3_arrow_rests_at_the_mix_then_swings_to_the_result():
    at = run_page("t3")
    assert 'primer-qubit-arrow prepared"' in arrow_markup(at)
    assert angle(arrow_markup(at), "to") == 90
    at.button(key="t3_measure1").click().run()
    html = arrow_markup(at)
    assert 'primer-qubit-arrow snapped"' in html
    assert angle(html, "from") == 90
    assert angle(html, "to") == (0 if at.session_state["t3_snapped"] == "UP"
                                 else 180)


def test_t3_measuring_the_same_qubit_again_does_not_replay_the_swing():
    at = run_page("t3")
    at.button(key="t3_measure1").click().run()
    before = arrow_markup(at)
    at.button(key="t3_again").click().run()
    assert arrow_markup(at) == before


def test_t3_each_fresh_measurement_replays_the_swing():
    at = run_page("t3")
    at.slider(key="t3_p").set_value(100).run()      # always UP
    at.button(key="t3_measure1").click().run()
    first = arrow_markup(at)
    at.button(key="t3_measure1").click().run()
    assert arrow_markup(at) != first
