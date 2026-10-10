"""Checks for the shared building blocks in components/."""

from streamlit.testing.v1 import AppTest

import tutor


# ---- journey ---------------------------------------------------------------

def _journey_app():
    import streamlit as st
    from components import journey
    if st.button("go"):
        journey.record("preset", "t2", name="Pattern 1 Only")
        journey.record("measure", "t3", ups=3, downs=7)
    st.write(f"count={len(journey.events())}")


def test_journey_starts_empty_and_keeps_events_in_order():
    at = AppTest.from_function(_journey_app).run()
    assert at.markdown[0].value == "count=0"
    at.button[0].click().run()
    events = at.session_state["journey"]
    assert [e["type"] for e in events] == ["preset", "measure"]
    assert events[0]["page"] == "t2" and events[0]["details"] == {"name": "Pattern 1 Only"}
    assert events[1]["details"] == {"ups": 3, "downs": 7}
    assert events[0]["time"] <= events[1]["time"]


# ---- chat panel ------------------------------------------------------------

def _chat_app():
    from components.chat_panel import chat_panel, model_picker
    model_picker()
    chat_panel({
        "page_id": "t1", "page_title": "Bits", "controls": "a switch",
        "settings_lines": ["Switch is ON"], "results_lines": [],
        "revealed": True,
    }, starter_questions=["What is a bit?"])


def _texts(elements):
    return " ".join(e.value for e in elements)


def test_chat_says_tutor_is_off_when_ollama_is_off():
    at = AppTest.from_function(_chat_app).run()
    assert not at.exception
    assert "The tutor is off" in _texts(at.info)
    assert len(at.chat_input) == 0


def test_chat_heading_is_ask_your_own_questions(ollama):
    at = AppTest.from_function(_chat_app).run()
    assert "Ask your own questions" in _texts(at.subheader)


def test_model_picker_defaults_to_first_model(ollama):
    at = AppTest.from_function(_chat_app).run()
    assert at.selectbox[0].value == "model-newest"


def test_typed_question_gets_a_streamed_answer(ollama):
    at = AppTest.from_function(_chat_app).run()
    at.chat_input[0].set_value("Why?").run()
    chat = at.session_state["chat_t1"]
    assert [m["role"] for m in chat] == ["user", "assistant"]
    assert chat[1]["content"] == "Hello there."
    assert chat[0]["settings"] == "Switch is ON"
    assert "Switch is ON" in ollama.requests[-1]["messages"][0]["content"]


def test_question_is_recorded_in_the_journey(ollama):
    at = AppTest.from_function(_chat_app).run()
    at.chat_input[0].set_value("Why?").run()
    event = at.session_state["journey"][-1]
    assert event["type"] == "chat_question" and event["page"] == "t1"
    assert event["details"]["question"] == "Why?"
    assert event["details"]["answer"] == "Hello there."


def test_starter_question_button_asks_it(ollama):
    at = AppTest.from_function(_chat_app).run()
    at.button(key="suggest_t1_0_0").click().run()
    assert at.session_state["chat_t1"][0]["content"] == "What is a bit?"


def test_dropped_answer_leaves_no_half_conversation(ollama):
    ollama.mode = "drop"
    at = AppTest.from_function(_chat_app).run()
    at.chat_input[0].set_value("Why?").run()
    assert at.session_state["chat_t1"] == []
    assert "dropped" in _texts(at.error)


def _seeded_app():
    from components.chat_panel import chat_panel, model_picker
    model_picker()
    chat_panel({
        "page_id": "tyu", "chat_key": "tyu_q1", "page_title": "Test",
        "controls": "answer boxes", "settings_lines": [], "revealed": True,
    }, seed_message="Question: X. My answer: Y.")


def test_seed_message_is_sent_as_the_first_question(ollama):
    at = AppTest.from_function(_seeded_app).run()
    chat = at.session_state["chat_tyu_q1"]
    assert chat[0]["content"] == "Question: X. My answer: Y."
    assert chat[1]["role"] == "assistant"


# ---- prediction gate -------------------------------------------------------

def _gate_app():
    import streamlit as st
    from components.prediction_gate import prediction_gate
    theta = st.slider("theta", 0, 180, 90)
    gate = prediction_gate("g", (theta,))
    gate.ask_choice("Same or different?", ["same", "different"])
    if gate.run_button("Run"):
        st.write("RESULT")
    st.write(f"prediction={gate.prediction} just_ran={gate.just_ran}")


def _shown(at):
    return " ".join(m.value for m in at.markdown)


def test_gate_is_locked_until_a_prediction_is_made():
    at = AppTest.from_function(_gate_app).run()
    assert len(at.button) == 0
    assert "Make a prediction" in " ".join(i.value for i in at.info)
    assert "prediction=None" in _shown(at)


def test_gate_runs_after_prediction_and_click():
    at = AppTest.from_function(_gate_app).run()
    at.radio[0].set_value("different").run()
    assert "RESULT" not in _shown(at)
    at.button[0].click().run()
    assert "RESULT" in _shown(at)
    assert "prediction=different just_ran=True" in _shown(at)
    at.run()   # an unrelated rerun keeps the result but is not a new run
    assert "RESULT" in _shown(at) and "just_ran=False" in _shown(at)


def test_gate_relocks_and_clears_prediction_when_settings_change():
    at = AppTest.from_function(_gate_app).run()
    at.radio[0].set_value("different").run()
    at.button[0].click().run()
    at.slider[0].set_value(45).run()
    assert "RESULT" not in _shown(at)
    assert "prediction=None" in _shown(at)
    assert at.radio[0].value == "Choose one"
    assert "Settings changed" in " ".join(i.value for i in at.info)


def test_changing_settings_before_running_keeps_the_prediction():
    at = AppTest.from_function(_gate_app).run()
    at.radio[0].set_value("same").run()
    at.slider[0].set_value(45).run()
    assert "prediction=same" in _shown(at)


def _number_gate_app():
    import streamlit as st
    from components.prediction_gate import prediction_gate
    gate = prediction_gate("n", ())
    gate.ask_number("How many heads out of 100?", 0, 100)
    if gate.run_button("Slap"):
        st.write("RESULT")
    st.write(f"prediction={gate.prediction}")


def test_number_gate_unlocks_once_a_number_is_entered():
    at = AppTest.from_function(_number_gate_app).run()
    assert len(at.button) == 0
    at.number_input[0].set_value(50).run()
    assert "prediction=50" in _shown(at)
    at.button[0].click().run()
    assert "RESULT" in _shown(at)


# ---- state card ------------------------------------------------------------

import pytest

from components import state_card


def test_sphere_angles_for_pure_and_equal_states():
    assert state_card.sphere_angles(1, 0) == (0.0, 0.0)
    assert state_card.sphere_angles(0, 1)[0] == pytest.approx(180.0)
    assert state_card.sphere_angles(1, 1)[0] == pytest.approx(90.0)


def test_sphere_angles_match_the_qubit_formula():
    theta, phi = state_card.sphere_angles(0.8, 0.6, 30)
    assert theta == pytest.approx(73.74, abs=0.01)
    assert phi == pytest.approx(30.0)


def test_opposite_signs_count_as_a_half_turn_of_phase():
    assert state_card.sphere_angles(1, -1) == (pytest.approx(90.0), pytest.approx(180.0))


def test_no_state_when_both_amplitudes_are_zero():
    assert state_card.sphere_angles(0, 0) is None


def _card_app():
    from components.state_card import state_card
    state_card(0, 0, labels=("Pattern 1", "Pattern 2"))


def test_state_card_with_no_state_says_so():
    at = AppTest.from_function(_card_app).run()
    assert not at.exception
    assert "No state yet" in " ".join(c.value for c in at.caption)


# ---- state that must survive leaving a page and coming back -----------------

def _two_page_app():
    import streamlit as st
    from components import layout
    from components.prediction_gate import prediction_gate

    def page_a():
        st.title("A")
        layout.keep("a_slider", 50)
        value = st.slider("s", 0, 100, key="a_slider")
        gate = prediction_gate("a_gate", (value,))
        gate.ask_choice("Q?", ["yes", "no"])
        if gate.run_button("Run"):
            st.write("RESULT")
        if st.button("to B", key="to_b"):
            st.switch_page(pb)

    def page_b():
        st.title("B")
        if st.button("to A", key="to_a"):
            st.switch_page(pa)

    pa = st.Page(page_a, title="A", default=True)
    pb = st.Page(page_b, title="B")
    st.navigation([pa, pb]).run()


def test_settings_prediction_and_result_survive_a_visit_to_another_page():
    at = AppTest.from_function(_two_page_app).run()
    at.slider(key="a_slider").set_value(70).run()
    at.radio(key="a_gate_prediction").set_value("yes").run()
    at.button(key="a_gate_run").click().run()
    at.button(key="to_b").click().run()
    assert at.title[0].value == "B"
    at.button(key="to_a").click().run()
    assert at.title[0].value == "A"
    assert at.slider(key="a_slider").value == 70
    assert at.radio(key="a_gate_prediction").value == "yes"
    assert "RESULT" in _shown(at)
    assert len(at.warning) == 0


def test_prediction_cannot_be_edited_after_the_result_is_shown():
    at = AppTest.from_function(_gate_app).run()
    assert not at.radio[0].disabled
    at.radio[0].set_value("different").run()
    at.button[0].click().run()
    assert at.radio[0].disabled
    at.slider[0].set_value(45).run()          # new settings: predict afresh
    assert not at.radio[0].disabled


def test_number_prediction_is_locked_after_the_result_too():
    at = AppTest.from_function(_number_gate_app).run()
    at.number_input[0].set_value(50).run()
    at.button[0].click().run()
    assert at.number_input[0].disabled


def _reset_gate_app():
    import streamlit as st
    from components.prediction_gate import prediction_gate, reset_gate
    st.button("clear", on_click=reset_gate, args=("r",))
    gate = prediction_gate("r", ())
    gate.ask_number("How many?", 0, 100)
    if gate.run_button("Run"):
        st.write("RESULT")


def test_reset_gate_hides_the_result_and_clears_the_prediction():
    at = AppTest.from_function(_reset_gate_app).run()
    at.number_input[0].set_value(50).run()
    at.button(key="r_run").click().run()
    assert "RESULT" in _shown(at)
    at.button[0].click().run()
    assert "RESULT" not in _shown(at)
    assert at.number_input[0].value is None and not at.number_input[0].disabled


# ---- who sees what the student types ---------------------------------------

CLOUD = {"name": "big-model:cloud", "remote_host": "https://ollama.com"}


def _captions(at):
    return " ".join(c.value for c in at.caption)


def test_local_model_says_answers_stay_on_this_computer(ollama):
    at = AppTest.from_function(_chat_app).run()
    assert "running on this computer" in _captions(at)


def test_cloud_model_picked_in_local_ollama_gets_the_cloud_warning(ollama):
    ollama.models = ["local-model", CLOUD]
    at = AppTest.from_function(_chat_app).run()
    assert "running on this computer" in _captions(at)
    at.selectbox[0].set_value("big-model:cloud").run()
    assert "sent to Ollama's cloud service" in _captions(at)
    assert "running on this computer" not in _captions(at)


def test_model_list_is_not_fetched_again_on_every_redraw(ollama):
    at = AppTest.from_function(_chat_app).run()
    at.run()
    at.run()
    assert ollama.tag_requests == 1


# ---- class password ---------------------------------------------------------

def test_chat_is_locked_until_the_class_password_is_given(ollama, monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "open-sesame")
    tutor.load_settings()
    at = AppTest.from_function(_chat_app).run()
    assert len(at.chat_input) == 0
    # Inside a form, the typed text is sent together with the button press.
    at.text_input[0].set_value("wrong")
    at.button[0].click().run()
    assert "not right" in " ".join(e.value for e in at.error)
    assert len(at.chat_input) == 0 and ollama.requests == []
    at.text_input[0].set_value("open-sesame")
    at.button[0].click().run()
    assert len(at.chat_input) == 1


# ---- animations -------------------------------------------------------------

import numpy as np

from components import plots_waves
from physics import oscillators, phibit


def test_oscillator_animation_has_a_complete_frame_for_every_moment():
    t = np.linspace(0, 4 * np.pi, 30)
    x1, x2 = oscillators.positions(t, 40, -10)
    fig = plots_waves.oscillator_animation(t, x1, x2)
    assert len(fig.frames) == 30
    assert all(len(frame.data) == len(fig.data) for frame in fig.frames)
    play = fig.layout.updatemenus[0].buttons[0]
    assert set(play.args[0]) == {frame.name for frame in fig.frames}


def _chain_frames(a_left, a_right, wave_number, omega):
    x = np.arange(12.0)
    fine = np.linspace(0, 11, 50)
    cycle = np.linspace(0, 2 * np.pi / omega, 20, endpoint=False)
    u = np.array([phibit.displacement(x, t, a_left, a_right, 0, wave_number, omega)
                  for t in cycle])
    f = np.array([phibit.displacement(fine, t, a_left, a_right, 0, wave_number, omega)
                  for t in cycle])
    return u, fine, f


def test_chain_animation_has_a_complete_frame_for_every_moment():
    u, fine, f = _chain_frames(1, 0.5, phibit.DEFAULT_K, 1.5)
    fig = plots_waves.chain_animation(u, fine, f, nodes=[2.0])
    assert len(fig.frames) == 20
    assert all(len(frame.data) == len(fig.data) for frame in fig.frames)


def test_chain_weights_never_cross_even_for_short_wavelengths():
    # Real chain, fast driver, both waves on: neighbors move almost opposite.
    q = phibit.chain_wavenumber(3.9)
    u, _, _ = _chain_frames(1, 1, q, 3.9)
    scale = plots_waves.chain_scale(u)
    positions = np.arange(12) + scale * u
    assert np.all(np.diff(positions, axis=1) > 0.3)
    # Gentle waves keep the original size.
    gentle, _, _ = _chain_frames(1, 0, phibit.DEFAULT_K, 1.5)
    assert plots_waves.chain_scale(gentle) == plots_waves.CHAIN_SCALE
