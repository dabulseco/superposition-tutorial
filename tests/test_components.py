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
