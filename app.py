"""
Superposition vs. Mixture — an interactive simulation for undergraduates
=========================================================================

WHAT THIS APP TEACHES
---------------------
Students often believe a quantum superposition such as

        |psi> = (|0> + |1>) / sqrt(2)

is "really" either |0> or |1>, and we just don't know which. That belief
describes a *classical mixture*, not a superposition.

The two can give IDENTICAL results when measured along the z-axis (50/50),
but DIFFERENT results along any other axis. Measured along x, the
superposition gives "+" every time, while the mixture still gives 50/50.

This app lets students build both kinds of state, choose a measurement axis,
predict the outcome, and then "run the experiment" with simulated shots.

HOW TO RUN
----------
    pip install -r requirements.txt
    streamlit run app.py

THE PHYSICS IN ONE PARAGRAPH
----------------------------
Any spin-1/2 (two-level) state can be described by a "Bloch vector" r.
  * A pure state lies ON the surface of the Bloch sphere (|r| = 1).
  * A mixture lies INSIDE the sphere (|r| < 1).
If we measure along a unit axis n, the probability of getting "+" is

        P(+) = (1 + r . n) / 2

That single formula drives every number and plot in this app.

CODE LAYOUT
-----------
  Part 1: physics functions (no Streamlit, so they can be tested or reused
          by an AI agent)
  Part 2: plotting functions
  Part 3: the Streamlit page
  Part 4: "Ask the tutor" chat (the model logic lives in tutor.py)

ASK THE TUTOR
-------------
Students can type questions into a chat box at the bottom of the page.
By default, answers come from a language model running LOCALLY through
Ollama, so nothing leaves the computer. When an Ollama API key is set (for
hosting the app online), answers come from Ollama's cloud service instead,
and the tutor can be locked behind a class password. Students can download
the conversation as a web page or a Markdown file. See tutor.py for setup.
"""

import hmac
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import tutor   # the Ollama tutor (tutor.py, in this same folder)

# Where Q&A is saved if logging is switched on in the sidebar.
LOG_FILE = Path(__file__).parent / "logs" / "tutor_log.jsonl"

# Colors used consistently everywhere: one for the superposition, one for
# the mixture. Both are distinguishable for common color-vision differences.
COLOR_PURE = "#1f5fbf"      # deep blue  -> superposition (pure state)
COLOR_MIX = "#c98a00"       # ochre      -> classical mixture
COLOR_AXIS = "#2e8b57"      # green      -> measurement axis


# =============================================================================
# PART 1: PHYSICS
# =============================================================================

def unit_vector(polar_deg: float, azimuth_deg: float) -> np.ndarray:
    """
    Turn two angles into a 3D unit vector (x, y, z).

    polar_deg   : angle down from the +z axis (0 = straight up, 180 = down)
    azimuth_deg : angle around the z-axis, measured from +x toward +y
    """
    theta = np.radians(polar_deg)
    phi = np.radians(azimuth_deg)
    return np.array([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta),
    ])


def bloch_vector_pure(theta_deg: float, phi_deg: float) -> np.ndarray:
    """
    Bloch vector of the PURE superposition state

        |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>

    The vector sits on the surface of the sphere (length 1).
    theta sets the balance between |0> and |1>; phi is the relative phase.
    """
    return unit_vector(theta_deg, phi_deg)


def bloch_vector_mixture(theta_deg: float) -> np.ndarray:
    """
    Bloch vector of the CLASSICAL MIXTURE that has the same z-statistics:

        "|0> with probability cos^2(theta/2),
         |1> with probability sin^2(theta/2)"

    A mixture has no phase relationship between |0> and |1>, so its
    x and y components are zero. Only the z component survives.
    """
    p0 = np.cos(np.radians(theta_deg) / 2) ** 2
    p1 = 1 - p0
    return np.array([0.0, 0.0, p0 - p1])   # z = P(0) - P(1)


def density_matrix(r: np.ndarray) -> np.ndarray:
    """
    Convert a Bloch vector into the 2x2 density matrix

        rho = (I + rx*X + ry*Y + rz*Z) / 2

    The OFF-DIAGONAL entries are the "coherences". They are nonzero for a
    superposition and exactly zero for the mixture. They are what makes
    interference possible.
    """
    rx, ry, rz = r
    return 0.5 * np.array([
        [1 + rz,        rx - 1j * ry],
        [rx + 1j * ry,  1 - rz],
    ])


def probability_plus(r: np.ndarray, n: np.ndarray) -> float:
    """Born rule for spin-1/2: probability of '+' along axis n is (1 + r.n)/2."""
    p = 0.5 * (1 + float(np.dot(r, n)))
    return float(np.clip(p, 0.0, 1.0))   # clip guards against rounding error


def simulate_shots(p_plus: float, n_shots: int, seed: int) -> int:
    """
    Simulate n_shots individual measurements. Each shot is random; only the
    statistics are predictable. Returns how many shots came out '+'.
    """
    rng = np.random.default_rng(seed)
    return int(rng.binomial(n_shots, p_plus))


def describe_state(theta_deg: float, phi_deg: float) -> str:
    """Write the pure state in Dirac notation, for display."""
    a = np.cos(np.radians(theta_deg) / 2)
    b = np.sin(np.radians(theta_deg) / 2)
    return (rf"|\psi\rangle = {a:.3f}\,|0\rangle + "
            rf"e^{{i\,{phi_deg:.0f}^\circ}}\,{b:.3f}\,|1\rangle")


# =============================================================================
# PART 2: PLOTS
# =============================================================================

def _arrow(fig, vec, color, name):
    """Draw a vector from the origin as a line with a cone for the arrowhead."""
    fig.add_trace(go.Scatter3d(
        x=[0, vec[0]], y=[0, vec[1]], z=[0, vec[2]],
        mode="lines", line=dict(color=color, width=7), name=name,
    ))
    if np.linalg.norm(vec) > 0.05:   # skip arrowhead for (near) zero vectors
        fig.add_trace(go.Cone(
            x=[vec[0]], y=[vec[1]], z=[vec[2]],
            u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=0.15, anchor="tip",
            colorscale=[[0, color], [1, color]], showscale=False,
            showlegend=False,
        ))


def bloch_sphere_figure(r_pure, r_mix, n_axis) -> go.Figure:
    """3D Bloch sphere with both state vectors and the measurement axis."""
    fig = go.Figure()

    # Translucent sphere
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
    fig.add_trace(go.Surface(
        x=np.cos(u) * np.sin(v), y=np.sin(u) * np.sin(v), z=np.cos(v),
        opacity=0.08, showscale=False, hoverinfo="skip",
        colorscale=[[0, "#888"], [1, "#888"]],
    ))

    # Reference axes with state labels at the ends
    labels = {"|0⟩": (0, 0, 1.2), "|1⟩": (0, 0, -1.2),
              "|+⟩ (x)": (1.25, 0, 0), "|+i⟩ (y)": (0, 1.25, 0)}
    for a, b in [((-1, 0, 0), (1, 0, 0)), ((0, -1, 0), (0, 1, 0)),
                 ((0, 0, -1), (0, 0, 1))]:
        fig.add_trace(go.Scatter3d(
            x=[a[0], b[0]], y=[a[1], b[1]], z=[a[2], b[2]], mode="lines",
            line=dict(color="#aaa", width=2), showlegend=False,
            hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(
        x=[p[0] for p in labels.values()], y=[p[1] for p in labels.values()],
        z=[p[2] for p in labels.values()], mode="text",
        text=list(labels.keys()), showlegend=False, hoverinfo="skip"))

    # Measurement axis drawn as a dashed line through the whole sphere
    fig.add_trace(go.Scatter3d(
        x=[-n_axis[0], n_axis[0]], y=[-n_axis[1], n_axis[1]],
        z=[-n_axis[2], n_axis[2]], mode="lines",
        line=dict(color=COLOR_AXIS, width=4, dash="dash"),
        name="Measurement axis"))

    _arrow(fig, r_pure, COLOR_PURE, "Superposition (on the surface)")
    _arrow(fig, r_mix, COLOR_MIX, "Mixture (inside the sphere)")

    fig.update_layout(
        height=460, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.02),
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False), aspectmode="cube",
            camera=dict(eye=dict(x=1.4, y=1.1, z=0.7)),
        ),
    )
    return fig


def results_figure(plus_pure, plus_mix, n_shots) -> go.Figure:
    """Bar chart of simulated '+' and '-' counts for both states."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Superposition", x=["+", "−"],
                         y=[plus_pure, n_shots - plus_pure],
                         marker_color=COLOR_PURE))
    fig.add_trace(go.Bar(name="Mixture", x=["+", "−"],
                         y=[plus_mix, n_shots - plus_mix],
                         marker_color=COLOR_MIX))
    fig.update_layout(barmode="group", height=320,
                      yaxis_title="Number of shots",
                      xaxis_title="Measurement outcome",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def sweep_figure(r_pure, r_mix, meas_azimuth, current_polar) -> go.Figure:
    """
    P(+) as the measurement axis tilts from +z (0 deg) to -z (180 deg).
    This shows at a glance where the two states agree and where they differ.
    """
    angles = np.linspace(0, 180, 181)
    p_pure = [probability_plus(r_pure, unit_vector(a, meas_azimuth))
              for a in angles]
    p_mix = [probability_plus(r_mix, unit_vector(a, meas_azimuth))
             for a in angles]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=angles, y=p_pure, name="Superposition",
                             line=dict(color=COLOR_PURE, width=3)))
    fig.add_trace(go.Scatter(x=angles, y=p_mix, name="Mixture",
                             line=dict(color=COLOR_MIX, width=3, dash="dot")))
    fig.add_vline(x=current_polar, line_color=COLOR_AXIS, line_dash="dash",
                  annotation_text="your axis")
    fig.update_layout(height=320, yaxis_range=[-0.02, 1.02],
                      xaxis_title="Measurement axis tilt from +z (degrees)",
                      yaxis_title="P(+)",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


# =============================================================================
# PART 3: THE STREAMLIT PAGE
# =============================================================================

def main():
    st.set_page_config(page_title="Superposition vs. mixture", layout="wide")
    tutor.load_settings()   # pick up any change to the key or password
    st.title("Superposition vs. mixture")
    st.write(
        "Two states can give the same results along one axis and different "
        "results along another. Build a state, choose how to measure it, "
        "predict, then run the experiment."
    )

    # ---------------- Sidebar: controls ----------------
    with st.sidebar:
        st.header("1. Build the state")
        theta = st.slider("Balance θ between |0⟩ and |1⟩ (degrees)",
                          0, 180, 90,
                          help="0 = all |0⟩, 90 = equal parts, 180 = all |1⟩")
        phi = st.slider("Relative phase φ (degrees)", 0, 359, 0,
                        help="Only the superposition has a phase. "
                             "The mixture ignores this slider.")

        st.header("2. Choose the measurement axis")
        preset = st.radio("Quick choice",
                          ["Along z", "Along x", "Along y", "Custom"],
                          horizontal=True)
        if preset == "Along z":
            m_polar, m_azim = 0, 0
        elif preset == "Along x":
            m_polar, m_azim = 90, 0
        elif preset == "Along y":
            m_polar, m_azim = 90, 90
        else:
            m_polar = st.slider("Axis tilt from +z (degrees)", 0, 180, 90)
            m_azim = st.slider("Axis rotation around z (degrees)", 0, 359, 0)

        st.header("3. Experiment settings")
        n_shots = st.select_slider("Shots per state",
                                   [10, 100, 1000, 10000], value=1000)
        seed = st.number_input("Random seed (change to rerun)", 0, 9999, 1)

        st.header("4. Tutor")
        model, ollama_error = tutor_model_picker()
        if tutor.HOSTED:
            # A web host wipes its files on restart, so a log there would
            # be lost. Students download the conversation instead.
            save_log = False
        else:
            save_log = st.checkbox(
                "Save questions and answers to a local log file", value=False,
                help=f"Saved on this computer only, at {LOG_FILE}")

    # ---------------- Physics for the current settings ----------------
    r_pure = bloch_vector_pure(theta, phi)
    r_mix = bloch_vector_mixture(theta)
    n_axis = unit_vector(m_polar, m_azim)
    p_pure = probability_plus(r_pure, n_axis)
    p_mix = probability_plus(r_mix, n_axis)

    # Filled in only after the student runs the experiment.
    plus_pure = plus_mix = None

    # ---------------- Layout ----------------
    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("The two states")
        st.latex(describe_state(theta, phi))
        p0 = np.cos(np.radians(theta) / 2) ** 2
        st.markdown(
            f"**Mixture:** a box that holds |0⟩ with probability "
            f"{p0:.2f} and |1⟩ with probability {1 - p0:.2f}. "
            f"Every particle is definitely one or the other."
        )
        st.plotly_chart(bloch_sphere_figure(r_pure, r_mix, n_axis),
                        width="stretch")

    with right:
        # Predict-observe-explain: ask for a prediction before revealing data.
        st.subheader("Predict")
        prediction = st.radio(
            "Measured along this axis, the two states will give…",
            ["Choose one",
             "the same results",
             "different results",
             "can't tell without measuring"],
            key="prediction",
        )

        st.subheader("Observe")
        if prediction == "Choose one":
            st.info("Make a prediction to unlock the experiment.")
        else:
            if st.button("Run the experiment", type="primary"):
                st.session_state["ran"] = True
            if st.session_state.get("ran"):
                plus_pure = simulate_shots(p_pure, n_shots, seed)
                plus_mix = simulate_shots(p_mix, n_shots, seed + 1)
                st.plotly_chart(results_figure(plus_pure, plus_mix, n_shots),
                                width="stretch")
                c1, c2 = st.columns(2)
                c1.metric("Superposition: P(+) theory", f"{p_pure:.3f}",
                          f"measured {plus_pure / n_shots:.3f}",
                          delta_color="off")
                c2.metric("Mixture: P(+) theory", f"{p_mix:.3f}",
                          f"measured {plus_mix / n_shots:.3f}",
                          delta_color="off")

                same = abs(p_pure - p_mix) < 0.01
                truth = "the same results" if same else "different results"
                if prediction == truth:
                    st.success(f"Your prediction matches: {truth}.")
                else:
                    st.warning(f"Theory says {truth}. What did you expect, "
                               f"and why might it differ?")

    # ---------------- Explain section ----------------
    st.divider()
    st.subheader("Explain")
    e1, e2 = st.columns(2)

    with e1:
        st.markdown("**P(+) for every possible measurement tilt**")
        st.plotly_chart(sweep_figure(r_pure, r_mix, m_azim, m_polar),
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
            rho = density_matrix(r)
            st.markdown(f"*{label}*")
            st.latex(_matrix_latex(rho))

        st.markdown(
            "**Things to try**\n"
            "1. Set θ = 90°, φ = 0°. Measure along z, then along x.\n"
            "2. Keep measuring along x and change φ to 180°. "
            "What happens to the superposition? To the mixture?\n"
            "3. Set φ = 90° and measure along y.\n"
            "4. Is there any θ where the two states can never be told apart?"
        )

    # ---------------- Ask the tutor ----------------
    # Everything the tutor needs to know about what the student sees now.
    sim = {
        "theta": theta, "phi": phi,
        "state_text": (f"{np.cos(np.radians(theta) / 2):.3f}|0> + "
                       f"e^(i*{phi} deg) {np.sin(np.radians(theta) / 2):.3f}|1>"),
        "p0": float(p0),
        "m_polar": m_polar, "m_azim": m_azim, "axis_name": preset,
        "prediction": prediction,
        "experiment_ran": plus_pure is not None,
        "n_shots": n_shots,
        "p_pure": p_pure, "p_mix": p_mix,
        "plus_pure": plus_pure, "plus_mix": plus_mix,
    }
    tutor_chat(model, ollama_error, sim, save_log)


# =============================================================================
# PART 4: ASK THE TUTOR
# =============================================================================

def tutor_model_picker():
    """
    Sidebar dropdown of Ollama models.
    Local: the installed models; the default is the first one, i.e. the top
    line of `ollama list`. Hosted: the short list in tutor.HOSTED_MODELS.
    Returns (model name or None, error message or None).
    """
    try:
        models = tutor.list_models()
    except tutor.OllamaUnavailable as err:
        st.warning(str(err))
        return None, str(err)

    if not models:
        msg = ("The Ollama cloud service listed no models." if tutor.HOSTED else
               "Ollama is running but has no models. Run `ollama pull llama3.2`, then reload.")
        st.warning(msg)
        return None, msg

    if tutor.HOSTED:
        model = st.selectbox("Model (Ollama cloud)", models, index=0)
    else:
        model = st.selectbox("Model (installed in Ollama)", models, index=0,
                             help="Listed in the same order as `ollama list`.")
    return model, None


def tutor_unlocked() -> bool:
    """
    Ask for the class password, if one is set (APP_PASSWORD).
    Returns True once the student may use the tutor.
    """
    if not tutor.APP_PASSWORD or st.session_state.get("tutor_unlocked"):
        return True

    with st.form("tutor_password"):
        entered = st.text_input("Class password", type="password",
                                help="Ask your instructor for it.")
        submitted = st.form_submit_button("Unlock the tutor")

    if submitted:
        # compare_digest takes the same time whether or not the guess is close.
        if hmac.compare_digest(entered.encode(), tutor.APP_PASSWORD.encode()):
            st.session_state["tutor_unlocked"] = True
            st.rerun()
        st.error("That password is not right.")
    return False


def suggested_questions(chat):
    """
    Buttons for questions to consider next. Before the first question these
    are fixed starters; afterwards the tutor proposes them with each answer.
    Clicking one asks it.
    """
    questions = chat[-1].get("suggestions", []) if chat else tutor.STARTER_QUESTIONS
    if not questions:
        return

    def ask(question):
        st.session_state["clicked_question"] = question

    st.caption("Questions to consider next (click one to ask it):" if chat
               else "Not sure where to start? Try one of these:")
    for i, question in enumerate(questions):
        st.button(question, key=f"suggest_{len(chat)}_{i}",
                  on_click=ask, args=(question,))


def download_buttons(chat):
    """Buttons that save the conversation as a web page or Markdown file."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    col_html, col_md, _ = st.columns([1, 1, 2])
    col_html.download_button(
        "Download as HTML", tutor.conversation_html(chat),
        file_name=f"tutor-conversation-{stamp}.html", mime="text/html",
        help="A web page that opens in any browser.")
    col_md.download_button(
        "Download as Markdown", tutor.conversation_markdown(chat),
        file_name=f"tutor-conversation-{stamp}.md", mime="text/markdown",
        help="Plain text that is easy to analyze later.")


def tutor_chat(model, ollama_error, sim, save_log):
    """Chat box where students ask questions about the simulation."""
    st.divider()
    st.subheader("Ask the tutor")
    if tutor.HOSTED:
        st.caption("Ask about anything on this page. Your questions are sent "
                   "to Ollama's cloud service to be answered, so don't type "
                   "personal information. Answers can be wrong, so check "
                   "them against the simulation.")
    else:
        st.caption("Ask about anything on this page. Answers come from a model "
                   "running on this computer and can be wrong, so check them "
                   "against the simulation.")

    # The conversation is kept for this browser session only.
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    for msg in st.session_state["chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if model is None:
        st.info(f"The tutor is off. {ollama_error}")
        return

    if not tutor_unlocked():
        return

    # A question is either typed, or picked by clicking a suggested one.
    typed = st.chat_input("e.g. Why does the mixture stay at 50/50 along x?")
    clicked = st.session_state.pop("clicked_question", None)
    question = typed or clicked
    if question:
        # The time and settings are kept for the downloadable transcript.
        st.session_state["chat"].append({
            "role": "user", "content": question,
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "settings": tutor.settings_text(sim),
            "suggested": not typed,
        })
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                suggestions = []
                answer = st.write_stream(tutor.stream_answer(
                    model, tutor.build_system_prompt(sim),
                    st.session_state["chat"], suggestions))
            except tutor.OllamaUnavailable as err:
                st.error(str(err))
                st.session_state["chat"].pop()   # drop the unanswered question
                return

        st.session_state["chat"].append(
            {"role": "assistant", "content": answer, "model": model,
             "suggestions": suggestions})
        if save_log:
            tutor.log_interaction(LOG_FILE, model, sim, question, answer)

    suggested_questions(st.session_state["chat"])

    if st.session_state["chat"]:
        download_buttons(st.session_state["chat"])
        if st.button("Clear conversation"):
            st.session_state["chat"] = []
            st.rerun()


def _matrix_latex(m: np.ndarray) -> str:
    """Format a 2x2 complex matrix as LaTeX, hiding zero imaginary parts."""
    def fmt(z):
        re, im = round(z.real, 3), round(z.imag, 3)
        if abs(im) < 1e-3:
            return f"{re:.3f}"
        sign = "+" if im >= 0 else "-"
        return f"{re:.3f} {sign} {abs(im):.3f}i"
    return (r"\begin{pmatrix}" + f"{fmt(m[0,0])} & {fmt(m[0,1])} \\\\ "
            f"{fmt(m[1,0])} & {fmt(m[1,1])}" + r"\end{pmatrix}")


if __name__ == "__main__":
    main()
