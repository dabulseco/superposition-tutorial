"""
pages/t4_phibits.py — Topic 4: Phi-Bit Systems ("Sound-like Waves")
===================================================================

WHAT THIS PAGE TEACHES
----------------------
Superposition is not only for tiny quantum objects. On a chain of weights
and springs, a wave traveling left (State 0) and a wave traveling right
(State 1) can be present at the same time, in any amounts. Equal amounts
give a standing wave. The two amplitudes and their relative phase describe
the chain exactly the way two amplitudes and a phase describe a qubit, so
the same state card and sphere appear here.

The page also says where the likeness ends: this is a classical wave, so
both parts can be watched at once and nothing snaps when you look.

The physics is in physics/phibit.py.
"""

import numpy as np
import streamlit as st

from components import journey, layout, plots_waves
from components.chat_panel import chat_panel
from components.prediction_gate import prediction_gate
from components.quick_check import quick_check
from components.state_card import state_card
from physics import phibit

PAGE_ID = "t4"
N_WEIGHTS = 12
PRESETS = {"left": ("State 0 (100% Left)", (100, 0)),
           "right": ("State 1 (100% Right)", (0, 100)),
           "super": ("Superposition (Both!)", (100, 100))}
PREDICT_ANSWER = "They slide along the chain; the wave stays standing"
state = st.session_state

state.setdefault("t4_left", 100)
state.setdefault("t4_right", 0)


def set_mix(left: int, right: int, preset: str) -> None:
    """Move both amplitude sliders (used by the preset buttons)."""
    state["t4_left"], state["t4_right"] = left, right
    journey.record("preset", PAGE_ID, name=preset, left=left, right=right)


# Another page (a "revisit" link) or the prediction below may ask this page
# to open on a particular mix. Apply it before the sliders are drawn.
if layout.arrival_preset(PAGE_ID) == "superposition":
    state["t4_left"], state["t4_right"] = PRESETS["super"][1]
if "t4_pending" in state:
    state["t4_left"], state["t4_right"] = state.pop("t4_pending")

text = layout.page_header(PAGE_ID)
picture, controls = st.columns([1.5, 1])

# ---------------- Controls ----------------
with controls:
    st.subheader(text["presets_heading"])
    for name, (label, (left, right)) in PRESETS.items():
        st.button(label, key=f"t4_preset_{name}", width="stretch",
                  on_click=set_mix, args=(left, right, label))
    frequency = st.slider("Driving Force Frequency (Motor Speed)", 0.5, 4.0,
                          1.5, step=0.1, key="t4_freq",
                          help="Slow on the left, fast on the right.")

    st.subheader(text["mixer_heading"])
    st.markdown(text["mixer_text"])
    left_pct = st.slider("LEFT Wave Amplitude", 0, 100, key="t4_left",
                         format="%d%%")
    right_pct = st.slider("RIGHT Wave Amplitude", 0, 100, key="t4_right",
                          format="%d%%")
    delta = st.slider("Relative phase δ between the two waves (degrees)",
                      0, 359, 0, key="t4_delta",
                      help="Shifts the right wave relative to the left one. "
                           "At 0 the page behaves like the original primer.")

    with st.expander("Go deeper: a real chain"):
        real_chain = st.toggle(
            "Use the chain's real frequency–wavelength relation",
            key="t4_real")
        low, high = phibit.chain_band()
        st.caption(
            f"On a real chain the driving frequency sets the wavelength, and "
            f"the side springs set a lowest frequency that can travel "
            f"({low:.1f} here; the highest is {high:.1f}). Switch this on "
            f"and move the frequency slider.")

# ---------------- Physics for the current settings ----------------
a_left, a_right = left_pct / 100, right_pct / 100

wave_number = phibit.DEFAULT_K
can_travel = True
if real_chain:
    wave_number = phibit.chain_wavenumber(frequency)
    can_travel = wave_number is not None

status = phibit.classify(left_pct, right_pct)
share = phibit.share_of_state_1(a_left, a_right)
standing = can_travel and a_left == a_right and a_left > 0
nodes = (phibit.node_positions(wave_number, delta, N_WEIGHTS - 1)
         if standing else np.array([]))

# One full cycle of the motion, as animation frames.
N_FRAMES = 40
weights_x = np.arange(N_WEIGHTS, dtype=float)
fine_x = np.linspace(0, N_WEIGHTS - 1, 200)
cycle = np.linspace(0, 2 * np.pi / frequency, N_FRAMES, endpoint=False)
if can_travel:
    frames_u = np.array([phibit.displacement(
        weights_x, t, a_left, a_right, delta, wave_number, frequency)
        for t in cycle])
    frames_fine = np.array([phibit.displacement(
        fine_x, t, a_left, a_right, delta, wave_number, frequency)
        for t in cycle])
else:
    frames_u = np.zeros((N_FRAMES, N_WEIGHTS))
    frames_fine = np.zeros((N_FRAMES, len(fine_x)))

# A faster motor plays the same cycle in less time, as in the original.
frame_ms = int(np.clip(5200 / (frequency * N_FRAMES), 30, 300))


def motion_summary() -> str:
    """One sentence saying what the animation shows, for screen readers."""
    if not can_travel:
        return "the weights stay still because no wave can travel."
    if status == phibit.LABEL_NONE:
        return "the weights stay still because both waves are off."
    if status == phibit.LABEL_STATE0:
        return "a wave travels steadily to the left along the chain."
    if status == phibit.LABEL_STATE1:
        return "a wave travels steadily to the right along the chain."
    if standing:
        return ("the wave stands in place: some weights swing widely while "
                "the still points (dotted lines) do not move at all.")
    stronger = "left" if a_left > a_right else "right"
    return (f"a lumpy wave drifts to the {stronger}: its size rises and "
            f"falls as it goes, because the two waves are unequal.")


with picture:
    st.info(status)
    if not can_travel:
        st.warning(
            f"No traveling wave at this frequency. This chain only carries "
            f"waves with frequency between {low:.1f} and {high:.1f}.")
    st.plotly_chart(
        plots_waves.chain_animation(
            frames_u, fine_x, frames_fine, nodes=nodes, frame_ms=frame_ms,
            title="Chain of weights (top) and displacement graph (bottom)"),
        width="stretch")
    st.caption(f"Animation (press Play): {motion_summary()}")

    p_left, p_right, p_share = st.columns(3)
    p_left.metric("LEFT wave power", f"{a_left ** 2:.2f}",
                  help="Power goes as the amplitude squared.")
    p_right.metric("RIGHT wave power", f"{a_right ** 2:.2f}",
                   help="Power goes as the amplitude squared.")
    p_share.metric("Share of State 1", "—" if share is None else f"{share:.0%}",
                   help="RIGHT power divided by total power: the same "
                        "formula as a qubit's probability of |1⟩.")

    if standing:
        shift = np.radians(delta) / (2 * wave_number)
        moved = ("have not moved (phase is 0)" if delta == 0 else
                 f"have moved {shift:.2f} weight spacings to the left")
        st.caption(
            f"Still points (dotted lines) are at positions "
            f"{', '.join(f'{x:.2f}' for x in nodes)} (weight 1 is at 0, "
            f"weight 12 at 11). Compared with phase 0 they {moved}.")

    st.markdown("**Predict**")
    gate = prediction_gate("t4_predict", ())
    gate.ask_choice(
        "If you change the phase while the mix is 50/50, what happens to "
        "the still points?",
        [PREDICT_ANSWER,
         "They disappear; the wave starts traveling",
         "Nothing changes at all",
         "They stay put; the wave gets taller"])
    if gate.run_button("Set a 50/50 mix and try it"):
        matched = gate.prediction == PREDICT_ANSWER
        if gate.just_ran:
            journey.record("prediction", PAGE_ID, question="phase and nodes",
                           prediction=gate.prediction,
                           outcome=PREDICT_ANSWER, matched=matched)
            state["t4_pending"] = PRESETS["super"][1]
            st.rerun()
        st.markdown("The mix is now 50/50. **Move the phase slider** and "
                    "watch the dotted lines.")
        if matched:
            st.success("Your prediction matches: the still points slide "
                       "along the chain, and the wave is still a standing "
                       "wave.")
        else:
            st.warning("Move the phase slider and watch the dotted lines. "
                       "How does what you see compare with your prediction?")

# Remember setting changes for the journey (once per change).
setting = (left_pct, right_pct, delta, frequency, real_chain)
if state.get("t4_last_setting") not in (None, setting):
    journey.record("mixer_set", PAGE_ID, left=left_pct, right=right_pct,
                   phase=delta, frequency=frequency, real_chain=real_chain,
                   status=status)
state["t4_last_setting"] = setting

# ---------------- Explain ----------------
st.divider()
st.subheader("Explain")
card_side, notes_side = st.columns([1.4, 1])
with card_side:
    state_card(a_left, a_right, delta,
               labels=("State 0 (left wave)", "State 1 (right wave)"))
with notes_side:
    st.markdown("**Same and different**")
    st.markdown(text["same_different"])
    layout.things_to_try(text)


# ---------------- Ask your own questions ----------------
def tutor_context() -> dict:
    """What the tutor is told about this page right now."""
    rules = []
    if not gate.ran:
        rules.append(
            "The student has not yet answered this page's prediction "
            "question (what happens to the still points when the phase "
            "changes at a 50/50 mix). Do not tell them the answer; help "
            "them reason it out.")
    results = [f"Status box: {status}"]
    if share is not None:
        results.append(f"Share of State 1 = {share:.2f}")
    if standing:
        results.append("Standing wave; still points at x = "
                       + ", ".join(f"{x:.2f}" for x in nodes))
    if not can_travel:
        results.append("No traveling wave: the driving frequency is outside "
                       f"the chain's band ({low:.2f} to {high:.2f})")
    return {
        "page_id": PAGE_ID,
        "page_title": text["title"],
        "controls": "three presets, the driving-frequency slider, LEFT and "
                    "RIGHT amplitude sliders, the relative-phase slider, the "
                    "chain animation and displacement graph, power and share "
                    "readouts, the state card, a Go deeper switch for a real "
                    "chain",
        "settings_lines": [
            f"LEFT wave amplitude {left_pct}%, RIGHT wave amplitude "
            f"{right_pct}%, relative phase {delta} deg",
            f"Driving frequency {frequency:.1f}; real-chain option "
            f"{'on' if real_chain else 'off'}",
            f"Student's prediction about phase and still points: "
            f"{gate.prediction or 'none yet'}",
        ],
        "results_lines": results,
        "revealed": True,
        "extra_rules": rules,
    }


quick_check(PAGE_ID)
chat_panel(tutor_context(), starter_questions=text["starter_questions"])
layout.prev_next(PAGE_ID)
