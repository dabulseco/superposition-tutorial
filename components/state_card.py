"""
components/state_card.py — one picture for every topic
======================================================

The oscillator patterns, the qubit, and the phi-bit are all "two basic
states combined with two amplitudes and a relative phase". This card draws
any of them the same way: two amplitude bars, and a dot on a sphere like
the qubit's Bloch sphere. Seeing the same card on three pages is how
students notice that the same mathematics describes all three.

THE FORMULA
-----------
For amplitudes a0 and a1 of the two basic states and relative phase delta:

    theta = 2 * arctan(|a1| / |a0|)     0 deg = all state 0, 180 = all state 1
    phi   = delta                       (plus 180 deg if a0 and a1 have
                                         opposite signs, since a minus sign
                                         is a half-turn of phase)
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import plots
from components.theme import COLOR_STATE0, COLOR_STATE1
from physics.mixture import unit_vector


def sphere_angles(amp0: float, amp1: float, phase_deg: float = 0.0):
    """
    Where the state sits on the sphere: (theta_deg, phi_deg).
    Returns None when both amplitudes are zero (there is no state to draw).
    """
    if amp0 == 0 and amp1 == 0:
        return None
    # arctan2 copes with amp0 = 0, where a plain division would fail.
    theta = 2 * np.degrees(np.arctan2(abs(amp1), abs(amp0)))
    flip = 180.0 if amp0 * amp1 < 0 else 0.0
    return float(theta), float((phase_deg + flip) % 360)


def state_card(amp0: float, amp1: float, phase_deg: float = 0.0,
               labels=("State 0", "State 1")) -> None:
    """Draw the amplitude bars and the sphere for one two-part state."""
    st.markdown("**State card: the same picture on every topic**")
    bars, sphere = st.columns(2)
    angles = sphere_angles(amp0, amp1, phase_deg)

    with bars:
        fig = go.Figure(go.Bar(
            x=list(labels), y=[abs(amp0), abs(amp1)],
            marker_color=[COLOR_STATE0, COLOR_STATE1],
            text=[f"{abs(amp0):.3g}", f"{abs(amp1):.3g}"], textposition="auto"))
        fig.update_layout(height=260, yaxis_title="Amplitude (size)",
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")

    with sphere:
        ends = {labels[0]: (0, 0, 1.25), labels[1]: (0, 0, -1.25)}
        fig = plots.bloch_sphere_base(ends, height=260)
        if angles is not None:
            plots.arrow(fig, unit_vector(*angles), COLOR_STATE0, "State")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

    if angles is None:
        st.caption("No state yet: both amplitudes are zero.")
        return
    theta, phi = angles
    share = amp1 ** 2 / (amp0 ** 2 + amp1 ** 2)
    st.caption(
        f"Bars: {labels[0]} amplitude {abs(amp0):.3g}, {labels[1]} amplitude "
        f"{abs(amp1):.3g}. Sphere: the arrow is tilted {theta:.0f}° from the "
        f"top ({labels[0]}) toward the bottom ({labels[1]}), turned {phi:.0f}° "
        f"around. Share of {labels[1]} (amplitude squared): {share:.0%}.")
