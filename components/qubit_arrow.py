"""
components/qubit_arrow.py — the animated qubit arrow on Topic 3
===============================================================

The qubit's sphere seen from the side, drawn as a flat picture with HTML
and CSS only (no JavaScript, no image files):

  * prepared  -> the arrow rests at the tilt the slider set
  * measured  -> the arrow swings from that tilt to UP (top) or DOWN
                 (bottom), goes a little past, and comes back to rest

WHY A FLAT PICTURE
------------------
On Topic 3 there is no relative phase yet, so the arrow never leaves one
flat slice of the sphere. Drawing just that slice loses nothing, and it
lets the browser show the arrow moving, which the 3D chart cannot do. The
full 3D sphere is still on the page, in the state card.

THE ANGLE
---------
The tilt is theta, measured from the top: 0 deg = certainly UP,
90 deg = an equal mix, 180 deg = certainly DOWN. (physics/qubit.py turns
the slider's probability into theta.)

HOW IT IS DRAWN
---------------
Streamlit removes SVG drawings and inline styles from HTML it is given, so
the picture is built from plain boxes (a round one for the sphere, a thin
one for the arrow's shaft, a triangle for its head), and the angles are
written into the style sheet rather than onto the arrow itself.

HOW THE SWING REPLAYS
---------------------
Streamlit only redraws this piece of the page when its HTML changes. Two
UP results in a row would give identical HTML, and the second measurement
would look as if nothing had happened. So the HTML also carries the
measurement count (`shot`): a fresh measurement changes it and the swing
plays again; measuring the SAME qubit again does not, and the arrow stays
where it is, as it should.

ACCESSIBILITY
-------------
  * People whose device asks for reduced motion get the arrow already at
    its final position.
  * The drawing carries a text label for screen readers; the page also
    gives the tilt in words.
"""

import streamlit as st

from components.theme import COLOR_PURE

OVERSHOOT = 0.14     # how far past the pole the arrow goes, as a share of the swing
REBOUND = 0.05       # how far it comes back the other way before resting

ARROW_CSS = """
<style>
.primer-qubit {
  position: relative; width: 260px; height: 280px; margin: 0 auto;
  font: 600 15px system-ui, sans-serif;
}
.primer-qubit div { position: absolute; box-sizing: border-box; }
.primer-qubit .sphere {
  left: 35px; top: 45px; width: 190px; height: 190px; border-radius: 50%;
  border: 2px solid currentColor; opacity: 0.5;
}
.primer-qubit .equator {
  left: 35px; top: 116px; width: 190px; height: 48px; border-radius: 50%;
  border: 1.5px dashed currentColor; opacity: 0.3;
}
.primer-qubit .axis {
  left: 129px; top: 45px; width: 0; height: 190px;
  border-left: 1.5px dashed currentColor; opacity: 0.3;
}
.primer-qubit .pole { left: 0; width: 260px; text-align: center; }
.primer-qubit .pole.up { top: 12px; }
.primer-qubit .pole.down { top: 246px; }
.primer-qubit .pole.reached { color: __COLOR__; font-weight: 800; }

.primer-qubit-arrow {
  left: 0; top: 0; width: 260px; height: 280px;
  transform-origin: 130px 140px; transform: rotate(var(--to));
}
.primer-qubit-arrow .shaft {
  left: 127px; top: 66px; width: 6px; height: 76px; border-radius: 3px;
  background: __COLOR__;
}
.primer-qubit-arrow .head {
  left: 119px; top: 45px; width: 0; height: 0;
  border-left: 11px solid transparent; border-right: 11px solid transparent;
  border-bottom: 24px solid __COLOR__;
}
.primer-qubit-arrow .hub {
  left: 123px; top: 133px; width: 14px; height: 14px; border-radius: 50%;
  background: __COLOR__;
}

/* Measured: swing to the pole, a little past it, and back. */
.primer-qubit-arrow.snapped { animation: primer-qubit-snap 0.85s ease-in-out 1 both; }
@keyframes primer-qubit-snap {
  0%, 12% { transform: rotate(var(--from)); }
  55%     { transform: rotate(var(--over)); }
  78%     { transform: rotate(var(--back)); }
  100%    { transform: rotate(var(--to)); }
}

/* Devices set to reduce motion: the arrow is simply at its new position. */
@media (prefers-reduced-motion: reduce) {
  .primer-qubit-arrow.snapped { animation: none; }
}
</style>
""".replace("__COLOR__", COLOR_PURE)


def arrow_html(prepared_deg: float, snapped: str | None = None,
               shot: int = 0) -> str:
    """
    The qubit picture as HTML.

    prepared_deg : tilt of the prepared state from the top, in degrees
    snapped      : None before a measurement, or "UP" / "DOWN" after one
    shot         : how many fresh measurements have been made (see the
                   note at the top on replaying the swing)
    """
    if snapped is None:
        state, start, end = "prepared", prepared_deg, prepared_deg
        label = (f"A qubit arrow tilted {prepared_deg:.0f} degrees from the "
                 f"top (UP)")
    else:
        state, start = "snapped", prepared_deg
        end = 0.0 if snapped == "UP" else 180.0
        label = (f"A qubit arrow that swung from {prepared_deg:.0f} degrees "
                 f"to point straight {snapped}")
    swing = end - start
    # The angles go into the style sheet (see "How it is drawn" above).
    angles = (f"--from: {start:g}deg; --over: {end + OVERSHOOT * swing:g}deg; "
              f"--back: {end - REBOUND * swing:g}deg; --to: {end:g}deg;")
    up_class = "pole up" + (" reached" if snapped == "UP" else "")
    down_class = "pole down" + (" reached" if snapped == "DOWN" else "")

    return f"""{ARROW_CSS}
<style>.primer-qubit-arrow {{ {angles} }}</style>
<div class="primer-qubit" role="img" aria-label="{label}">
  <div class="sphere"></div><div class="equator"></div><div class="axis"></div>
  <div class="{up_class}">UP |0⟩</div>
  <div class="{down_class}">DOWN |1⟩</div>
  <div class="primer-qubit-arrow {state}" data-shot="{shot}">
    <div class="shaft"></div><div class="head"></div><div class="hub"></div>
  </div>
</div>"""


def qubit_arrow(prepared_deg: float, snapped: str | None = None,
                shot: int = 0) -> None:
    """Draw the qubit picture on the page."""
    st.html(arrow_html(prepared_deg, snapped, shot))
