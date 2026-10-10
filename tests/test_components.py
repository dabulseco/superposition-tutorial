"""Checks for the shared building blocks in components/."""

from streamlit.testing.v1 import AppTest


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
