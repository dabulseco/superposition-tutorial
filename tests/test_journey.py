"""Checks for the My Journey record, its downloads, and its page."""

from streamlit.testing.v1 import AppTest

from components import chat_panel, journey, layout
from tests.test_pages import all_text, run_page, texts

NAMES = layout.PAGE_NAMES

EVENTS = [
    {"time": "2026-10-09T10:00:00+00:00", "page": "t1", "type": "page_visit",
     "details": {}},
    {"time": "2026-10-09T10:01:00+00:00", "page": "t1",
     "type": "measure_100_coins",
     "details": {"prediction": 50, "heads": 47, "off_by": 3}},
    {"time": "2026-10-09T10:02:00+00:00", "page": "t3b", "type": "run",
     "details": {"theta": 90, "phi": 0, "axis": "Along x", "shots": 1000,
                 "prediction": "the same results",
                 "outcome": "different results", "matched": False,
                 "plus_superposition": 1000, "plus_mixture": 503}},
    {"time": "2026-10-09T10:03:00+00:00", "page": "tyu", "type": "tyu_submit",
     "details": {"question_id": "q1", "question": "What is a superposition state?",
                 "attempt": 1, "answer": "Two states <script>alert(1)</script>",
                 "confidence": 4, "feedback": "Good start. What about measuring?",
                 "feedback_mode": "guided"}},
    {"time": "2026-10-09T10:04:00+00:00", "page": "t4", "type": "chat_question",
     "details": {"question": "Why does it stand still?",
                 "answer": "What do the two waves do at a still point?",
                 "model": "m"}},
    {"time": "2026-10-09T10:05:00+00:00", "page": "t2", "type": "something_new",
     "details": {"value": 3}},
]


def test_every_event_gets_a_readable_line():
    lines = [journey.describe(e, NAMES) for e in EVENTS]
    assert lines[0] == "Opened this page"
    assert "Predicted 50 heads out of 100" in lines[1] and "47" in lines[1]
    assert "different results" in lines[2] and "did not match" in lines[2]
    assert "attempt 1" in lines[3].lower()
    assert "Why does it stand still?" in lines[4]
    assert "something_new" in lines[5]          # unknown types still show up


def test_markdown_contains_answer_feedback_and_chat():
    md = journey.to_markdown(EVENTS, NAMES)
    assert "What is a superposition state?" in md
    assert "Good start. What about measuring?" in md
    assert "Confidence: 4 of 5" in md
    assert "Why does it stand still?" in md
    assert "What do the two waves do at a still point?" in md
    assert "1 · Bits & Superposition" in md


def test_html_escapes_what_the_student_typed():
    page = journey.to_html(EVENTS, NAMES)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "Spelman College" in page            # attribution travels with it


def test_summary_counts_predictions_and_matches():
    summary = journey.summary(EVENTS)
    assert summary == {"topics": 1, "predictions": 2, "matched": 0,
                       "answers": 1, "questions": 1}


def test_empty_journey_downloads_do_not_break():
    assert "Nothing recorded" in journey.to_markdown([], NAMES)
    assert "Nothing recorded" in journey.to_html([], NAMES)


# ---- the page ---------------------------------------------------------------

def test_my_journey_page_when_nothing_has_happened():
    at = run_page("journey")
    assert not at.exception
    assert "exists only in this browser tab" in all_text(at)
    assert "Nothing here yet" in texts(at.info)


def test_my_journey_page_shows_the_timeline_and_downloads():
    at = run_page("journey", journey=list(EVENTS), current_page="journey")
    assert not at.exception
    page = all_text(at)
    assert "Predicted 50 heads out of 100" in page
    assert "Good start. What about measuring?" in page
    labels = [b.label for b in at.get("download_button")]
    assert labels == ["Download as HTML", "Download as Markdown"]
    values = {m.label: m.value for m in at.metric}
    assert values["Answers submitted"] == "1"
    assert values["Predictions that matched"] == "0 of 2"


# ---- nothing is written to disk unless asked --------------------------------

def _chat_app():
    from components.chat_panel import chat_panel, model_picker
    model_picker()
    chat_panel({"page_id": "t1", "page_title": "Bits", "controls": "a switch",
                "settings_lines": ["Switch is ON"], "revealed": True})


def test_no_log_file_unless_the_box_is_ticked(ollama, monkeypatch, tmp_path):
    log = tmp_path / "logs" / "tutor_log.jsonl"
    monkeypatch.setattr(chat_panel, "LOG_FILE", log)
    at = AppTest.from_function(_chat_app).run()
    at.chat_input[0].set_value("Why?").run()
    assert not log.exists() and not log.parent.exists()

    at.sidebar.checkbox[0].check().run()
    at.chat_input[0].set_value("And how?").run()
    assert log.exists()
    assert '"page": "t1"' in log.read_text()
