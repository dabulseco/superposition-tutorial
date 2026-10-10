"""
views/t3b_superposition_vs_mixture.py — Go deeper: superposition vs. mixture
============================================================================

WHAT THIS PAGE TEACHES
----------------------
Students often believe a quantum superposition such as

        |psi> = (|0> + |1>) / sqrt(2)

is "really" either |0> or |1>, and we just don't know which. That belief
describes a *classical mixture*, not a superposition.

The two can give IDENTICAL results when measured along the z-axis (50/50),
but DIFFERENT results along any other axis. Measured along x, the
superposition gives "+" every time, while the mixture still gives 50/50.

Students build both kinds of state, choose a measurement axis, predict the
outcome, and then run the experiment with simulated shots. The physics is
in physics/mixture.py.
"""

import numpy as np
import streamlit as st

from components import journey, layout, plots
from components.chat_panel import chat_panel
from components.prediction_gate import prediction_gate
from physics import mixture

PAGE_ID = "t3b"
AXES = {"Along z": (0, 0), "Along x": (90, 0), "Along y": (90, 90)}

text = layout.page_header(PAGE_ID)
controls, picture, experiment = st.columns([0.8, 1.1, 1])

# ---------------- Controls ----------------
with controls:
    st.subheader("1. Build the state")
    layout.keep("t3b_theta", 90)
    theta = st.slider("Balance θ between |0⟩ and |1⟩ (degrees)", 0, 180,
                      key="t3b_theta",
                      help="0 = all |0⟩, 90 = equal parts, 180 = all |1⟩")
    layout.keep("t3b_phi", 0)
    phi = st.slider("Relative phase φ (degrees)", 0, 359, key="t3b_phi",
                    help="Only the superposition has a phase. "
                         "The mixture ignores this slider.")

    st.subheader("2. Choose the measurement axis")
    layout.keep("t3b_axis", "Along z")
    axis_name = st.radio("Quick choice", list(AXES) + ["Custom"],
                         horizontal=True, key="t3b_axis")
    if axis_name == "Custom":
        layout.keep("t3b_polar", 90)
        m_polar = st.slider("Axis tilt from +z (degrees)", 0, 180,
                            key="t3b_polar")
        layout.keep("t3b_azim", 0)
        m_azim = st.slider("Axis rotation around z (degrees)", 0, 359,
                           key="t3b_azim")
    else:
        m_polar, m_azim = AXES[axis_name]

    st.subheader("3. Experiment settings")
    layout.keep("t3b_shots", 1000)
    n_shots = st.select_slider("Shots per state", [10, 100, 1000, 10000],
                               key="t3b_shots")
    layout.keep("t3b_seed", 1)
    seed = st.number_input("Random seed (change to rerun)", min_value=0,
                           max_value=9999, step=1, key="t3b_seed")

# ---------------- Physics for the current settings ----------------
r_pure = mixture.bloch_vector_pure(theta, phi)
r_mix = mixture.bloch_vector_mixture(theta)
n_axis = mixture.unit_vector(m_polar, m_azim)
p_pure = mixture.probability_plus(r_pure, n_axis)
p_mix = mixture.probability_plus(r_mix, n_axis)
p0 = float(np.cos(np.radians(theta) / 2) ** 2)

# Filled in only after the student runs the experiment.
plus_pure = plus_mix = None

with picture:
    st.subheader("The two states")
    st.latex(mixture.describe_state(theta, phi))
    st.markdown(
        f"**Mixture:** a box that holds |0⟩ with probability {p0:.2f} and "
        f"|1⟩ with probability {1 - p0:.2f}. Every particle is definitely "
        f"one or the other.")
    st.plotly_chart(plots.bloch_sphere_figure(r_pure, r_mix, n_axis),
                    width="stretch")
    st.caption(
        f"Picture: the superposition's arrow reaches the surface of the "
        f"sphere; the mixture's arrow has length {np.linalg.norm(r_mix):.2f} "
        f"and lies on the vertical axis. The dashed line is the measurement "
        f"axis.")

# ---------------- Predict, then observe ----------------
with experiment:
    st.subheader("Predict")
    # Every setting the result depends on. Changing any of them after a run
    # hides the result until the student predicts again.
    gate = prediction_gate(PAGE_ID, (theta, phi, m_polar, m_azim, n_shots, seed))
    gate.ask_choice("Measured along this axis, the two states will give…",
                    ["the same results", "different results",
                     "can't tell without measuring"])

    st.subheader("Observe")
    if gate.run_button("Run the experiment"):
        plus_pure = mixture.simulate_shots(p_pure, n_shots, seed)
        plus_mix = mixture.simulate_shots(p_mix, n_shots, seed + 1)
        st.plotly_chart(plots.results_figure(plus_pure, plus_mix, n_shots),
                        width="stretch")
        c1, c2 = st.columns(2)
        c1.metric("Superposition: P(+) theory", f"{p_pure:.3f}",
                  f"measured {plus_pure / n_shots:.3f}", delta_color="off",
                  delta_arrow="off")
        c2.metric("Mixture: P(+) theory", f"{p_mix:.3f}",
                  f"measured {plus_mix / n_shots:.3f}", delta_color="off",
                  delta_arrow="off")

        same = abs(p_pure - p_mix) < 0.01
        truth = "the same results" if same else "different results"
        matched = gate.prediction == truth
        if matched:
            st.success(f"Your prediction matches: {truth}.")
        else:
            st.warning(f"Theory says {truth}. What did you expect, "
                       f"and why might it differ?")
        if gate.just_ran:
            journey.record(
                "run", PAGE_ID, theta=theta, phi=phi, axis=axis_name,
                shots=n_shots, prediction=gate.prediction, outcome=truth,
                matched=matched, plus_superposition=plus_pure,
                plus_mixture=plus_mix)

# ---------------- Explain ----------------
st.divider()
st.subheader("Explain")
e1, e2 = st.columns(2)

with e1:
    st.markdown("**P(+) for every possible measurement tilt**")
    st.plotly_chart(plots.sweep_figure(r_pure, r_mix, m_azim, m_polar),
                    width="stretch")
    st.caption("Where the curves meet, no experiment along that axis "
               "can tell the two states apart. Where they separate, "
               "one experiment is enough.")

with e2:
    st.markdown("**Density matrices**")
    st.caption("Diagonal entries are the z-probabilities. Off-diagonal "
               "entries (coherences) carry the phase. Only the "
               "superposition has them.")
    for label, r in [("Superposition", r_pure), ("Mixture", r_mix)]:
        st.markdown(f"*{label}*")
        st.latex(plots.matrix_latex(mixture.density_matrix(r)))
    layout.things_to_try(text)


# ---------------- Ask your own questions ----------------
def tutor_context() -> dict:
    """Everything the tutor needs to know about what the student sees now."""
    a = np.cos(np.radians(theta) / 2)
    b = np.sin(np.radians(theta) / 2)
    results = []
    if plus_pure is not None:
        results = [
            f"Theory: P(+) superposition = {p_pure:.3f}, "
            f"P(+) mixture = {p_mix:.3f}",
            f"Simulated results ({n_shots} shots each): superposition "
            f"{plus_pure} '+', mixture {plus_mix} '+'",
        ]
    return {
        "page_id": PAGE_ID,
        "page_title": text["title"],
        "controls": "sliders for theta and phi, the measurement axis, the "
                    "Bloch sphere, the P(+) sweep plot, the density matrices",
        "settings_lines": [
            f"theta = {theta} deg, phi = {phi} deg",
            f"Superposition: {a:.3f}|0> + e^(i*{phi} deg) {b:.3f}|1>",
            f"Mixture: |0> with probability {p0:.3f}, |1> with probability "
            f"{1 - p0:.3f}",
            f"Measurement axis: tilt {m_polar} deg from +z, rotated "
            f"{m_azim} deg around z ({axis_name})",
            f"Student's prediction: {gate.prediction or 'none yet'}",
        ],
        "results_lines": results,
        "revealed": plus_pure is not None,
        "hold_back": "the probabilities for the current axis or whether the "
                     "two states will differ there",
    }


chat_panel(tutor_context(), starter_questions=text["starter_questions"])
layout.prev_next(PAGE_ID)
