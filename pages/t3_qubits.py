"""
pages/t3_qubits.py — Topic 3: Electrons & Qubits
================================================

WHAT THIS PAGE TEACHES
----------------------
A qubit can be in a combination of UP and DOWN. The combination sets the
PROBABILITY of each result. A single measurement gives one result at
random and the state snaps to it; many measurements show the probability.

Students set the mix with one slider, predict how many UP results they
will get out of 100, measure, and watch the measured fraction settle
toward the probability they set as the sample grows.

The physics is in physics/qubit.py.
"""

import random

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import journey, layout, plots
from components.chat_panel import chat_panel
from components.prediction_gate import prediction_gate
from components.state_card import state_card
from components.theme import COLOR_AXIS, COLOR_PURE
from physics import qubit
from physics.mixture import unit_vector

PAGE_ID = "t3"
SPHERE_LABELS = {"UP |0⟩": (0, 0, 1.25), "DOWN |1⟩": (0, 0, -1.25)}
state = st.session_state

state.setdefault("t3_seed", random.randrange(1_000_000))
state.setdefault("t3_draws", 0)
state.setdefault("t3_snapped", None)     # None, "UP", or "DOWN"
state.setdefault("t3_outcomes", [])      # every result so far: 1 = UP, 0 = DOWN


def next_seed() -> int:
    """A new seed for each measurement."""
    state["t3_draws"] += 1
    return state["t3_seed"] + state["t3_draws"]


text = layout.page_header(PAGE_ID)
picture, controls = st.columns([1, 1])

# ---------------- Prepare ----------------
with controls:
    st.subheader(text["prepare_heading"])
    st.markdown(text["prepare_text"])
    percent_up = st.slider("100% DOWN  ←  →  100% UP", 0, 100, 50, key="t3_p",
                           format="%d%% UP")
    p_up = percent_up / 100
    st.markdown(f"**{percent_up}% UP / {100 - percent_up}% DOWN**")

    # A new mix is a new experiment: old results belong to the old mix.
    if state.get("t3_prepared") != percent_up:
        if state.get("t3_prepared") is not None and state["t3_outcomes"]:
            st.caption("You changed the mix, so the old results were cleared.")
        state["t3_prepared"] = percent_up
        state["t3_snapped"] = None
        state["t3_outcomes"] = []

    # ---------------- Measure ----------------
    st.subheader(text["experiment_heading"])
    st.markdown(text["experiment_text"])

    def measure_once():
        """Prepare one fresh qubit in the set mix and measure it."""
        result = int(qubit.measure_each(p_up, 1, next_seed())[0])
        state["t3_snapped"] = "UP" if result else "DOWN"
        state["t3_outcomes"] = state["t3_outcomes"] + [result]
        state["t3_message"] = "measured"
        journey.record("measure_1", PAGE_ID, percent_up=percent_up,
                       result=state["t3_snapped"])

    def measure_again():
        """Measure the SAME qubit again: it has already snapped."""
        state["t3_message"] = "again"
        journey.record("measure_same_again", PAGE_ID,
                       result=state["t3_snapped"])

    def clear_data():
        state["t3_outcomes"] = []
        state["t3_snapped"] = None
        state["t3_message"] = None

    st.button("Measure 1x", key="t3_measure1", on_click=measure_once)

    gate = prediction_gate("t3_predict", (percent_up,))
    gate.ask_number("Before you press Measure 100x: about how many UP "
                    "results out of 100?", 0, 100)
    if gate.run_button("Measure 100x"):
        if gate.just_ran:
            results = qubit.measure_each(p_up, 100, next_seed())
            state["t3_outcomes"] = state["t3_outcomes"] + [int(r) for r in results]
            state["t3_last100"] = int(results.sum())
            state["t3_snapped"] = None        # arrow goes back to the mix
            state["t3_message"] = "ran100"
            journey.record("measure_100", PAGE_ID, percent_up=percent_up,
                           prediction=gate.prediction,
                           ups=state["t3_last100"],
                           off_by=abs(state["t3_last100"] - gate.prediction))
        ups = state["t3_last100"]
        off_by = abs(ups - gate.prediction)
        st.markdown(f"This run: **{ups} UP** out of 100. You predicted "
                    f"{gate.prediction}, so you were off by {off_by}.")
        if off_by == 0:
            st.success("Your prediction matches exactly. Run it again: does "
                       "it match every time?")

snapped = state["t3_snapped"]
message = state.get("t3_message")

# ---------------- The picture ----------------
with picture:
    if snapped == "UP":
        theta = 0.0
    elif snapped == "DOWN":
        theta = 180.0
    else:
        theta = qubit.theta_from_probability(p_up)
    st.plotly_chart(
        plots.bloch_arrow_figure(unit_vector(theta, 0), "Qubit state",
                                 SPHERE_LABELS),
        width="stretch")
    if snapped:
        st.caption(f"Picture: after the measurement the arrow points "
                   f"straight {snapped} (tilted {theta:.0f}° from the top).")
    else:
        st.caption(f"Picture: the arrow is tilted {theta:.0f}° from the top "
                   f"(UP). The closer it is to a pole, the more likely that "
                   f"result.")

    if message == "measured" and snapped:
        ket = "|0⟩" if snapped == "UP" else "|1⟩"
        st.info(f"You measured! It snapped to: Spin {snapped} {ket}")
    elif message == "again" and snapped:
        st.info(f"Same result: {snapped}. The qubit already snapped to "
                f"{snapped}, so measuring it again gives {snapped} every "
                f"time. Press Measure 1x to prepare a fresh qubit.")
    elif message == "ran100":
        st.info(f"Ran 100 measurements! Resetting arrow to your "
                f"{percent_up}% UP mix.")
    else:
        st.info(f"Prepared in a {percent_up}% UP mix.")
    if snapped:
        st.button("Measure the same qubit again", key="t3_again",
                  on_click=measure_again)

# ---------------- Results ----------------
outcomes = state["t3_outcomes"]
total = len(outcomes)
ups_total = int(sum(outcomes))

st.divider()
st.subheader(f"Results Data ({total} total)")
bars_side, settle_side = st.columns(2)

with bars_side:
    st.plotly_chart(plots.count_bars(["UP", "DOWN"],
                                     [ups_total, total - ups_total]),
                    width="stretch")
    st.caption(f"Chart: UP: {ups_total}, DOWN: {total - ups_total}. "
               f"{text['sample_note']}")
    st.button("Clear Data", key="t3_clear", on_click=clear_data)

with settle_side:
    st.markdown("**Sample size: how the measured fraction settles**")
    fig = go.Figure()
    if total:
        fig.add_trace(go.Scatter(
            x=np.arange(1, total + 1), y=qubit.running_fraction(outcomes),
            mode="lines", line=dict(color=COLOR_PURE, width=2),
            name="Measured fraction UP"))
    fig.add_hline(y=p_up, line_color=COLOR_AXIS, line_dash="dash",
                  annotation_text="the probability you set")
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis_range=[-0.02, 1.02], showlegend=False,
                      xaxis_title="Number of measurements so far",
                      yaxis_title="Fraction UP")
    st.plotly_chart(fig, width="stretch")
    if total:
        st.caption(f"Chart: after {total} measurements the fraction UP is "
                   f"{ups_total / total:.3f}; you set {p_up:.2f}. Early on "
                   f"the line jumps around, then it settles.")
    else:
        st.caption("Chart: empty until you measure. The dashed line is the "
                   "probability you set.")

# ---------------- Explain ----------------
st.divider()
st.subheader("Explain")
card_side, try_side = st.columns([1.4, 1])
with card_side:
    # Amplitudes are the square roots of the probabilities.
    state_card(np.sqrt(p_up), np.sqrt(1 - p_up), labels=("UP", "DOWN"))
with try_side:
    layout.things_to_try(text)
    st.markdown(
        "The slider sets **probabilities**; the state card shows the "
        "matching **amplitudes** (their squares are the probabilities). "
        "One thing is still missing: the **relative phase**. A spinning "
        "coin has none, and it is what makes a superposition more than "
        "\"UP or DOWN, we just don't know which\".")
    if st.button("Go deeper: Superposition vs. mixture", key="t3_go_deeper",
                 type="primary"):
        journey.record("go_deeper_open", PAGE_ID)
        layout.go_to("t3b")


# ---------------- Ask your own questions ----------------
def tutor_context() -> dict:
    """What the tutor is told about this page right now."""
    return {
        "page_id": PAGE_ID,
        "page_title": text["title"],
        "controls": "the probability slider, the Bloch-sphere arrow, Measure "
                    "1x, Measure the same qubit again, Measure 100x, the "
                    "results bars, the sample-size chart, the state card",
        "settings_lines": [
            f"Prepared mix: {percent_up}% UP / {100 - percent_up}% DOWN "
            f"(arrow tilt theta = {qubit.theta_from_probability(p_up):.1f} deg)",
            f"Arrow right now: {'snapped to ' + snapped if snapped else 'at the prepared mix'}",
            f"Student's prediction for UP results out of 100: "
            f"{gate.prediction if gate.prediction is not None else 'none yet'}",
        ],
        "results_lines": [
            f"Results so far: {ups_total} UP and {total - ups_total} DOWN "
            f"out of {total} measurements",
        ] if total else [],
        "revealed": gate.ran,
        "hold_back": "how many UP results to expect out of 100 for this mix",
    }


chat_panel(tutor_context(), starter_questions=text["starter_questions"])
layout.prev_next(PAGE_ID)
