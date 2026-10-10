"""Checks for the animated light switch on Topic 1 (components/light_switch.py)."""

from components import light_switch
from tests.test_pages import all_text, run_page


def switch_markup(at):
    """The switch's HTML as drawn on the page."""
    return " ".join(h.proto.body for h in at.get("html")
                    if "primer-switch" in h.proto.body)


def label(html):
    return html.split('aria-label="')[1].split('"')[0]


def test_switch_that_is_on_shows_a_lit_bulb():
    html = light_switch.switch_html(True)
    assert 'class="primer-switch on"' in html
    assert "ON" in label(html) and "lit" in label(html)


def test_switch_that_is_off_shows_a_dark_bulb():
    html = light_switch.switch_html(False)
    assert 'class="primer-switch off"' in html
    assert "OFF" in label(html) and "dark" in label(html)


def test_switch_flips_with_a_short_animation_in_each_direction():
    html = light_switch.switch_html(True, flipped=True)
    assert 'class="primer-switch on flipped"' in html
    assert "primer-switch-flip-on" in html and "primer-switch-flip-off" in html
    assert "primer-bulb-light" in html and "primer-bulb-dim" in html


def test_switch_that_was_not_just_flipped_is_drawn_still():
    assert "flipped" not in light_switch.switch_html(True).split("</style>")[1]


def test_switch_respects_reduced_motion_and_uses_no_script():
    html = light_switch.switch_html(True)
    assert "prefers-reduced-motion: reduce" in html
    assert "<script" not in html.lower()


def test_same_setting_gives_identical_markup_so_the_flip_does_not_replay():
    assert light_switch.switch_html(True) == light_switch.switch_html(True)


# ---- on the page ------------------------------------------------------------

def test_t1_switch_drawing_follows_the_toggle():
    at = run_page("t1")
    assert 'class="primer-switch on"' in switch_markup(at)
    at.toggle(key="t1_switch_on").set_value(False).run()
    assert 'class="primer-switch off flipped"' in switch_markup(at)
    assert "The switch is **OFF**" in all_text(at)


def test_t1_switch_only_animates_on_the_run_where_it_was_flipped():
    at = run_page("t1")
    assert "flipped" not in switch_markup(at).split("</style>")[1]
    at.toggle(key="t1_switch_on").set_value(False).run()
    at.toggle(key="t1_pause").set_value(True).run()     # something unrelated
    assert 'class="primer-switch off"' in switch_markup(at)
