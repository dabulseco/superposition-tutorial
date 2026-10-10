"""
pages/t2_oscillators.py — Topic 2: Coupled Oscillators ("Jiggling Springs")
===========================================================================

WHAT THIS PAGE TEACHES
----------------------
Two weights joined by springs have two simple ways to move, called
patterns (normal modes): together, or opposite. Any other motion is a
SUPERPOSITION of the two, playing both at once.

Students pull the weights to starting positions, watch the motion, and read
a Fourier transform that measures how much of each pattern is playing. The
"state card" then shows the same motion as two amplitudes and a point on a
sphere, the picture that returns for the qubit and the phi-bit.

The physics is in physics/oscillators.py.
"""

import random

import numpy as np
import streamlit as st

from components import journey, layout, plots_waves
from components.chat_panel import chat_panel
from components.prediction_gate import prediction_gate
from components.state_card import state_card
from physics import oscillators as osc

PAGE_ID = "t2"
PRESETS = {"p1": ("Pattern 1 Only (Both Right)", (40, 40)),
           "p2": ("Pattern 2 Only (Opposite)", (40, -40))}
PREDICT_SETUP = (40, 0)      # weight 1 at Right 40, weight 2 at center
PREDICT_ANSWER = "Both, in equal amounts"
state = st.session_state

state.setdefault("t2_x1", 40)
state.setdefault("t2_x2", 40)
state.setdefault("t2_seed", random.randrange(1_000_000))


def side_label(x: int) -> str:
    """Slider value as the primer words it: Right 40, Left 40, Center 0."""
    return f"Right {x}" if x > 0 else f"Left {abs(x)}" if x < 0 else "Center 0"


def set_positions(x1: int, x2: int, preset: str) -> None:
    """Move both sliders (used by the preset buttons)."""
    state["t2_x1"], state["t2_x2"] = x1, x2
    journey.record("preset", PAGE_ID, name=preset, x1=x1, x2=x2)


def random_preset() -> None:
    state["t2_seed"] += 1
    set_positions(*osc.random_start(state["t2_seed"]),
                  preset="Random Superposition (Mix!)")


# The prediction's "set it up" button asks for these positions; they are
# applied here, before the sliders are drawn.
if "t2_pending" in state:
    state["t2_x1"], state["t2_x2"] = state.pop("t2_pending")

text = layout.page_header(PAGE_ID)
picture, controls = st.columns([1.4, 1])

# ---------------- Controls ----------------
with controls:
    st.subheader(text["positions_heading"])
    x1_0 = st.slider("Weight 1 (Left ← → Right)", -80, 80, key="t2_x1")
    st.caption(f"Weight 1 starts at **{side_label(x1_0)}**")
    x2_0 = st.slider("Weight 2 (Left ← → Right)", -80, 80, key="t2_x2")
    st.caption(f"Weight 2 starts at **{side_label(x2_0)}**")

    st.subheader(text["presets_heading"])
    for name, (label, (p1, p2)) in PRESETS.items():
        st.button(label, key=f"t2_preset_{name}", width="stretch",
                  on_click=set_positions, args=(p1, p2, label))
    st.button("Random Superposition (Mix!)", key="t2_preset_random",
              width="stretch", on_click=random_preset)
    st.caption(text["presets_note"])

    with st.expander("Go deeper: change the middle spring"):
        k_c = st.slider("Coupling spring stiffness", 0.5, 5.0, osc.DEFAULT_KC,
                        step=0.125, key="t2_kc",
                        help="How stiff the spring between the two weights "
                             "is. 2.625 is the primer's original value.")
        st.caption("Watch the spectrum: Pattern 2's peak moves when this "
                   "spring changes, but Pattern 1's does not. Why would the "
                   "middle spring not matter when the weights move together?")

# ---------------- Physics for the current settings ----------------
frequencies, _ = osc.normal_modes(osc.DEFAULT_K, k_c, osc.DEFAULT_M)
a1, a2 = osc.mode_amplitudes(x1_0, x2_0)

# About 12 seconds of animation: one full repeat of the default motion.
anim_t = np.linspace(0, 4 * np.pi, 150)
anim_x1, anim_x2 = osc.positions(anim_t, x1_0, x2_0, k_c=k_c)

# A longer recording for the Fourier transform (see physics/oscillators.py).
record_t = osc.sample_times()
record_x1, _ = osc.positions(record_t, x1_0, x2_0, k_c=k_c)
omega, amplitude = osc.spectrum(record_x1, record_t[1] - record_t[0])
peak_1 = osc.peak_height(omega, amplitude, frequencies[0])
peak_2 = osc.peak_height(omega, amplitude, frequencies[1])


def motion_summary() -> str:
    """One sentence saying what the animation shows, for screen readers."""
    if a1 == 0 and a2 == 0:
        return "both weights rest at the center and nothing moves."
    if a2 == 0:
        return "the weights swing left and right together (Pattern 1 only)."
    if a1 == 0:
        return ("the weights swing in opposite directions, toward and away "
                "from each other (Pattern 2 only).")
    return ("the weights follow an irregular-looking dance that is Pattern 1 "
            "and Pattern 2 playing at the same time.")


with picture:
    st.plotly_chart(plots_waves.oscillator_animation(anim_t, anim_x1, anim_x2),
                    width="stretch")
    st.caption(f"Animation (press Play): weight 1 is released from "
               f"{side_label(x1_0)} and weight 2 from {side_label(x2_0)}; "
               f"{motion_summary()}")
    m1, m2 = st.columns(2)
    m1.metric("Pattern 1 amplitude", f"{abs(a1):g}",
              f"frequency {frequencies[0]:.2f}", delta_color="off")
    m2.metric("Pattern 2 amplitude", f"{abs(a2):g}",
              f"frequency {frequencies[1]:.2f}", delta_color="off")

    st.markdown("**Predict**")
    gate = prediction_gate("t2_predict", ())
    gate.ask_choice(
        "With weight 1 at Right 40 and weight 2 at center, which patterns "
        "will light up?",
        ["Pattern 1 only", "Pattern 2 only", PREDICT_ANSWER,
         "Both, but more of one than the other"])
    if gate.run_button("Set it up and see"):
        matched = gate.prediction == PREDICT_ANSWER
        if gate.just_ran:
            journey.record("prediction", PAGE_ID, question="one-sided pull",
                           prediction=gate.prediction,
                           outcome=PREDICT_ANSWER, matched=matched)
            state["t2_pending"] = PREDICT_SETUP
            st.rerun()
        if matched:
            st.success("Your prediction matches: pulling one weight starts "
                       "both patterns in equal amounts (20 and 20).")
        else:
            st.warning("Look at the two amplitudes above for Right 40 and "
                       "Center 0. How do they compare with your prediction?")

# Remember slider changes for the journey (once per change, not per redraw).
setting = (x1_0, x2_0, k_c)
if state.get("t2_last_setting") not in (None, setting):
    journey.record("positions_set", PAGE_ID, x1=x1_0, x2=x2_0, coupling=k_c,
                   pattern_1=abs(a1), pattern_2=abs(a2))
state["t2_last_setting"] = setting

# ---------------- Explain ----------------
st.divider()
st.subheader("Explain")
trace_side, spectrum_side = st.columns(2)

with trace_side:
    st.markdown(f"**{text['trace_heading']}**")
    shown = record_t <= 25
    st.plotly_chart(plots_waves.trace_figure(record_t[shown], record_x1[shown]),
                    width="stretch")
    st.caption(text["trace_caption"])

with spectrum_side:
    st.markdown(f"**{text['spectrum_heading']}**")
    st.plotly_chart(plots_waves.spectrum_figure(omega, amplitude, frequencies),
                    width="stretch")
    st.caption(
        f"{text['spectrum_caption']} This is a real Fourier transform of "
        f"weight 1's motion: it finds peaks of height {peak_1:.1f} and "
        f"{peak_2:.1f} at frequencies {frequencies[0]:.2f} and "
        f"{frequencies[1]:.2f}, matching the two pattern amplitudes.")

card_side, try_side = st.columns([1.4, 1])
with card_side:
    state_card(a1, a2, labels=("Pattern 1", "Pattern 2"))
with try_side:
    layout.things_to_try(text)
    st.markdown(
        "The state card shows this motion as **two amplitudes**. A qubit "
        "(Topic 3) and a phi-bit (Topic 4) are described the same way.")


# ---------------- Ask your own questions ----------------
def tutor_context() -> dict:
    """What the tutor is told about this page right now."""
    rules = []
    if not gate.ran:
        rules.append(
            "The student has not yet answered this page's prediction "
            "question (weight 1 at Right 40, weight 2 at center). Do not "
            "tell them which patterns light up for that case; help them "
            "reason it out.")
    return {
        "page_id": PAGE_ID,
        "page_title": text["title"],
        "controls": "two starting-position sliders, three presets, the "
                    "animation, the plot of weight 1 over time, the Fourier "
                    "transform, the state card, a Go deeper slider for the "
                    "middle spring",
        "settings_lines": [
            f"Weight 1 starts at {side_label(x1_0)}, weight 2 at "
            f"{side_label(x2_0)} (released from rest)",
            f"Springs: wall springs k = 1, middle spring k_c = {k_c:g}, "
            f"masses m = 1",
            f"Pattern frequencies: omega_1 = {frequencies[0]:.3f}, "
            f"omega_2 = {frequencies[1]:.3f}",
            f"Student's prediction for the one-sided pull: "
            f"{gate.prediction or 'none yet'}",
        ],
        "results_lines": [
            f"Pattern amplitudes: A1 = {a1:g}, A2 = {a2:g}",
            f"Fourier transform peaks: {peak_1:.1f} at omega_1 and "
            f"{peak_2:.1f} at omega_2",
        ],
        "revealed": True,
        "extra_rules": rules,
    }


chat_panel(tutor_context(), starter_questions=text["starter_questions"])
layout.prev_next(PAGE_ID)
