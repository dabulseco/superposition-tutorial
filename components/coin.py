"""
components/coin.py — the animated coin on Topic 1
=================================================

A coin drawn with HTML and CSS only (no JavaScript, no image files):

  * not yet measured  -> it spins on its edge, too fast to read
  * measured          -> it lies flat showing H or T, after a short wobble
                         as it settles, like a real coin slapped onto a table

HOW IT WORKS
------------
The coin is a disc with two faces placed back to back (H and T). CSS turns
it in 3D. Spinning is one animation that repeats; settling is another that
plays once. Streamlit only redraws this piece of the page when its HTML
changes, so the wobble plays when the coin lands and not again each time a
slider somewhere else is moved.

ACCESSIBILITY
-------------
  * `paused=True` (the page's pause switch) stops the spin.
  * People whose device asks for reduced motion get a still coin
    automatically, with no wobble.
  * A stopped spin would freeze on H or T and look like a result, so a
    still, unmeasured coin shows "?" instead.
  * The coin carries a text label for screen readers; the page also says
    in words what the coin is doing.
"""

import streamlit as st

COIN_CSS = """
<style>
.primer-coin-stage {
  perspective: 700px; height: 150px; padding: 12px 0 0 12px;
}
.primer-coin {
  position: relative; width: 110px; height: 110px;
  transform-style: preserve-3d;
}
.primer-coin .face, .primer-coin .primer-coin-unknown {
  position: absolute; inset: 0; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font: 700 52px system-ui, sans-serif; color: #5b4300;
  border: 5px solid #9a7400;
  background: radial-gradient(circle at 35% 30%, #ffe89a, #e0b030 70%);
  box-shadow: 0 6px 10px rgba(0, 0, 0, 0.25);
  backface-visibility: hidden;
}
.primer-coin .face.tails { transform: rotateY(180deg); }
.primer-coin .primer-coin-unknown { display: none; }

/* Not yet measured: spin on its edge. */
.primer-coin.spinning { animation: primer-coin-spin 0.45s linear infinite; }

/* Measured: lie flat on the result, after a wobble that dies away. */
.primer-coin.landed.heads { animation: primer-coin-settle-heads 1s ease-out 1 both; }
.primer-coin.landed.tails { animation: primer-coin-settle-tails 1s ease-out 1 both; }

/* A still, unmeasured coin shows "?" rather than a frozen H or T. */
.primer-coin.paused { animation: none; }
.primer-coin.paused .face { display: none; }
.primer-coin.paused .primer-coin-unknown { display: flex; }

@keyframes primer-coin-spin {
  from { transform: rotateY(0deg); }
  to   { transform: rotateY(360deg); }
}
@keyframes primer-coin-settle-heads {
  0%   { transform: rotateY(0deg) rotateX(62deg) scale(1.12); }
  18%  { transform: rotateY(0deg) rotateX(-34deg) scale(1.04); }
  38%  { transform: rotateY(0deg) rotateX(20deg); }
  58%  { transform: rotateY(0deg) rotateX(-11deg); }
  78%  { transform: rotateY(0deg) rotateX(5deg); }
  100% { transform: rotateY(0deg) rotateX(0deg); }
}
@keyframes primer-coin-settle-tails {
  0%   { transform: rotateY(180deg) rotateX(62deg) scale(1.12); }
  18%  { transform: rotateY(180deg) rotateX(-34deg) scale(1.04); }
  38%  { transform: rotateY(180deg) rotateX(20deg); }
  58%  { transform: rotateY(180deg) rotateX(-11deg); }
  78%  { transform: rotateY(180deg) rotateX(5deg); }
  100% { transform: rotateY(180deg) rotateX(0deg); }
}

/* Devices set to reduce motion: no spin and no wobble. */
@media (prefers-reduced-motion: reduce) {
  .primer-coin.spinning { animation: none; }
  .primer-coin.spinning .face { display: none; }
  .primer-coin.spinning .primer-coin-unknown { display: flex; }
  .primer-coin.landed.heads { animation: none; transform: rotateY(0deg); }
  .primer-coin.landed.tails { animation: none; transform: rotateY(180deg); }
}
</style>
"""


def coin_html(result: str | None, paused: bool = False) -> str:
    """
    The coin as HTML.

    result : None while the coin is still spinning, or "HEADS" / "TAILS"
             once it has been slapped down
    paused : True to hold the spin still (the landed coin is already still)
    """
    if result is None:
        classes = "primer-coin spinning" + (" paused" if paused else "")
        label = ("A coin, paused before it is measured" if paused else
                 "A coin spinning too fast to tell heads from tails")
    else:
        classes = f"primer-coin landed {result.lower()}"
        label = f"A coin lying flat, showing {result}"

    return f"""{COIN_CSS}
<div class="primer-coin-stage">
  <div class="{classes}" role="img" aria-label="{label}">
    <div class="face heads">H</div>
    <div class="face tails">T</div>
    <div class="primer-coin-unknown">?</div>
  </div>
</div>"""


def coin(result: str | None, paused: bool = False) -> None:
    """Draw the coin on the page."""
    st.html(coin_html(result, paused))
