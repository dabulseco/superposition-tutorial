"""
components/light_switch.py — the animated light switch on Topic 1
=================================================================

A wall switch and a bulb drawn with HTML and CSS only (no JavaScript, no
image files):

  * ON   -> the lever is up and the bulb glows
  * OFF  -> the lever is down and the bulb is dark

When the student flips the switch, the lever moves and the bulb lights or
dims over about a third of a second. It then stays exactly as it is, which
is the point of the picture: a classical bit sits in one definite state.

HOW IT WORKS
------------
The drawing has a still version and a "flipped" version. The page asks for
the flipped version only on the run where the switch changed, so the lever
does not move by itself when the page first opens or when something else
on the page is used.

ACCESSIBILITY
-------------
  * People whose device asks for reduced motion get the still version.
  * The drawing carries a text label for screen readers; the page also
    says in words whether the switch is ON or OFF.
"""

import streamlit as st

SWITCH_CSS = """
<style>
.primer-switch {
  display: flex; align-items: center; gap: 36px; height: 130px;
  padding-left: 12px;
}
.primer-switch .plate {
  position: relative; width: 62px; height: 104px; border-radius: 8px;
  background: linear-gradient(#fafafa, #dcdcdc); border: 2px solid #9a9a9a;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.primer-switch .slot {
  position: absolute; left: 21px; top: 20px; width: 16px; height: 60px;
  border-radius: 8px; background: #4a4a4a;
}
.primer-switch .lever {
  position: absolute; left: 14px; top: 39px; width: 30px; height: 22px;
  border-radius: 6px; border: 2px solid #777777;
  background: linear-gradient(#ffffff, #c4c4c4);
  box-shadow: 0 3px 4px rgba(0, 0, 0, 0.35);
}
.primer-switch .lamp { position: relative; width: 74px; height: 96px; }
.primer-switch .bulb {
  position: absolute; left: 0; top: 0; width: 70px; height: 70px;
  border-radius: 50%; border: 2px solid #8a8a8a;
}
.primer-switch .base {
  position: absolute; left: 24px; top: 68px; width: 26px; height: 22px;
  border-radius: 0 0 6px 6px; border: 2px solid #777777;
  background: repeating-linear-gradient(#b5b5b5 0 4px, #8d8d8d 4px 7px);
}

/* The two resting states. */
.primer-switch.on .lever  { transform: translateY(-18px); }
.primer-switch.off .lever { transform: translateY(18px); }
.primer-switch.on .bulb {
  background: radial-gradient(circle at 38% 32%, #fffbe0, #ffd23c 70%);
  box-shadow: 0 0 26px 10px rgba(255, 205, 50, 0.65);
}
.primer-switch.off .bulb {
  background: radial-gradient(circle at 38% 32%, #f1f1f1, #b9b9b9 70%);
  box-shadow: none;
}

/* Just flipped: the lever moves, then the bulb follows. */
.primer-switch.on.flipped .lever  { animation: primer-switch-flip-on 0.18s ease-out 1 both; }
.primer-switch.off.flipped .lever { animation: primer-switch-flip-off 0.18s ease-out 1 both; }
.primer-switch.on.flipped .bulb   { animation: primer-bulb-light 0.3s ease-out 0.1s 1 both; }
.primer-switch.off.flipped .bulb  { animation: primer-bulb-dim 0.3s ease-out 0.1s 1 both; }

@keyframes primer-switch-flip-on {
  from { transform: translateY(18px); }
  to   { transform: translateY(-18px); }
}
@keyframes primer-switch-flip-off {
  from { transform: translateY(-18px); }
  to   { transform: translateY(18px); }
}
@keyframes primer-bulb-light {
  from { background: radial-gradient(circle at 38% 32%, #f1f1f1, #b9b9b9 70%);
         box-shadow: 0 0 0 0 rgba(255, 205, 50, 0); }
  to   { background: radial-gradient(circle at 38% 32%, #fffbe0, #ffd23c 70%);
         box-shadow: 0 0 26px 10px rgba(255, 205, 50, 0.65); }
}
@keyframes primer-bulb-dim {
  from { background: radial-gradient(circle at 38% 32%, #fffbe0, #ffd23c 70%);
         box-shadow: 0 0 26px 10px rgba(255, 205, 50, 0.65); }
  to   { background: radial-gradient(circle at 38% 32%, #f1f1f1, #b9b9b9 70%);
         box-shadow: 0 0 0 0 rgba(255, 205, 50, 0); }
}

/* Devices set to reduce motion: no movement, just the new state. */
@media (prefers-reduced-motion: reduce) {
  .primer-switch.flipped .lever, .primer-switch.flipped .bulb { animation: none; }
}
</style>
"""


def switch_html(on: bool, flipped: bool = False) -> str:
    """
    The switch and bulb as HTML.

    on      : True for ON (lever up, bulb lit), False for OFF
    flipped : True on the run where the student just flipped the switch,
              so the lever and bulb are shown changing
    """
    classes = ("primer-switch " + ("on" if on else "off")
               + (" flipped" if flipped else ""))
    label = ("A light switch set to ON beside a lit bulb" if on else
             "A light switch set to OFF beside a dark bulb")
    return f"""{SWITCH_CSS}
<div class="{classes}" role="img" aria-label="{label}">
  <div class="plate"><div class="slot"></div><div class="lever"></div></div>
  <div class="lamp"><div class="bulb"></div><div class="base"></div></div>
</div>"""


def light_switch(on: bool, flipped: bool = False) -> None:
    """Draw the switch and bulb on the page."""
    st.html(switch_html(on, flipped))
