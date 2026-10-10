"""
pages/test_understanding.py — Test Your Understanding
=====================================================

Three open questions answered in the student's own words. After each
submission the student gets formative feedback (a strength, a guiding
question, and a simulation to revisit) and can revise as often as they
like. Every submitted version is kept as a numbered attempt.

"Discuss this question" opens a chat that already knows the question and
the student's latest answer. The tutor there asks guiding questions; it is
told never to write the answer.

The questions and any rubric are in content/questions.yaml. The feedback
logic is in feedback.py.

WHAT IS STORED
--------------
Attempts live only in this browser tab's session. They appear on the My
Journey page, where the student can download them.
"""

from datetime import datetime, timezone

import streamlit as st

import feedback
import tutor
from components import journey, layout
from components.chat_panel import chat_panel, privacy_caption, tutor_unlocked

PAGE_ID = "tyu"
MAX_CHARS = 4000
NOT_RATED = "Not rated"
SAVED_NO_FEEDBACK = "Your answer is saved. Feedback is unavailable right now."
state = st.session_state

state.setdefault("tyu_attempts", {})     # question id -> list of attempts
state.setdefault("tyu_drafts", {})       # question id -> text being written

text = layout.page_header(PAGE_ID)

try:
    questions = feedback.load_questions(valid_pages=set(layout.PAGE_FILES))
except feedback.ContentError as err:
    st.error(str(err))
    st.stop()

model = state.get("tutor_model")
if model is None:
    st.info("The tutor is off, so answers are saved without feedback. "
            + (state.get("tutor_error") or ""))
# When hosted with a class password, feedback needs the password too, so
# strangers who find the link can't spend the tutor's quota.
unlocked = model is not None and tutor_unlocked(PAGE_ID)


def get_feedback(question: dict, answer: str):
    """Feedback for one answer, or None if the tutor can't give any now."""
    if not unlocked:
        return None
    try:
        with st.spinner("Reading your answer…"):
            return feedback.give_feedback(model, question, answer)
    except tutor.OllamaUnavailable:
        return None


def submit(question: dict, answer: str, confidence) -> None:
    """Save the answer as a new numbered attempt, then ask for feedback."""
    attempts = state["tyu_attempts"].setdefault(question["id"], [])
    attempt = {
        "number": len(attempts) + 1,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "answer": answer,
        "confidence": confidence,
        "feedback": None,
        "model": model,
    }
    # Saved BEFORE asking the model, so a failure there can't lose it.
    attempts.append(attempt)
    attempt["feedback"] = get_feedback(question, answer)
    result = attempt["feedback"] or {}
    journey.record(
        "tyu_submit", PAGE_ID, question_id=question["id"],
        question=question["text"], attempt=attempt["number"], answer=answer,
        confidence=confidence, feedback=result.get("text"),
        feedback_mode=result.get("mode"))


def show_attempt(attempt: dict) -> None:
    """One saved attempt with the feedback it received."""
    rated = (f" · confidence {attempt['confidence']} of 5"
             if attempt["confidence"] else "")
    st.markdown(f"**Attempt {attempt['number']}**{rated}")
    st.markdown("> " + attempt["answer"].replace("\n", "\n> "))
    if attempt["feedback"]:
        st.markdown(f"**Feedback:** {attempt['feedback']['text']}")
    else:
        st.caption(SAVED_NO_FEEDBACK)


st.caption(privacy_caption() + " Feedback can be wrong, so check it against "
           "the simulations.")

for number, question in enumerate(questions, start=1):
    qid = question["id"]
    attempts = state["tyu_attempts"].get(qid, [])
    with st.container(border=True):
        st.subheader(f"{number}. {question['text']}")

        draft = st.text_area(
            "Your answer", value=state["tyu_drafts"].get(qid, ""),
            key=f"tyu_draft_{qid}", max_chars=MAX_CHARS, height=140,
            placeholder="Write your answer in your own words.")
        # Kept outside the widget so the draft survives a visit to another page.
        state["tyu_drafts"][qid] = draft

        rate_side, button_side = st.columns([2, 1])
        rating = rate_side.select_slider(
            "How confident are you in this answer? (optional)",
            [NOT_RATED, "1", "2", "3", "4", "5"], key=f"tyu_confidence_{qid}",
            help="1 = I am guessing, 5 = I am certain.")
        confidence = None if rating == NOT_RATED else int(rating)

        label = "Submit" if not attempts else "Submit revised answer"
        if button_side.button(label, key=f"tyu_submit_{qid}", type="primary",
                              width="stretch"):
            if draft.strip():
                submit(question, draft.strip(), confidence)
                attempts = state["tyu_attempts"][qid]
            else:
                st.warning("Write an answer in the box first.")

        if not attempts:
            continue

        # ---- the latest attempt and its feedback ----
        latest = attempts[-1]
        st.markdown(f"**Feedback on attempt {latest['number']}**")
        if latest["feedback"]:
            st.info(latest["feedback"]["text"])
        else:
            st.warning(SAVED_NO_FEEDBACK)

        st.caption("Revisit a simulation, then revise your answer above and "
                   "submit again:")
        columns = st.columns(len(question["revisit"]) + 1)
        for i, link in enumerate(question["revisit"]):
            if columns[i].button(link["label"], key=f"tyu_revisit_{qid}_{i}"):
                journey.record("revisit_link", PAGE_ID, question_id=qid,
                               to=link["page"], label=link["label"])
                layout.go_to(link["page"], link.get("preset"))
        if columns[-1].button("Discuss this question", key=f"tyu_discuss_{qid}"):
            state["tyu_discussing"] = qid
            state["tyu_seed"] = True

        if len(attempts) > 1:
            with st.expander(f"Earlier attempts ({len(attempts) - 1})"):
                for attempt in attempts[:-1]:
                    show_attempt(attempt)

# ---------------- Discuss this question ----------------
by_id = {q["id"]: (n, q) for n, q in enumerate(questions, start=1)}
discussing = state.get("tyu_discussing")
if discussing in by_id and state["tyu_attempts"].get(discussing):
    number, question = by_id[discussing]
    latest = state["tyu_attempts"][discussing][-1]
    seed = None
    if state.pop("tyu_seed", False):
        seed = (f"Question: {question['text']}\n\nMy answer: "
                f"{latest['answer']}\n\nCan you help me think about how to "
                f"improve it?")
    revisit = "; ".join(link["label"] for link in question["revisit"])
    chat_panel({
        "page_id": PAGE_ID,
        "chat_key": f"{PAGE_ID}_{discussing}",
        "page_title": f"{text['title']}: question {number}",
        "controls": "the answer box, the feedback, and the buttons that "
                    f"reopen these simulations: {revisit}",
        "notes_pages": [link["page"] for link in question["revisit"]],
        "settings_lines": [
            f"Question under discussion: {question['text']}",
            f"The student has submitted {latest['number']} attempt(s). "
            f"Latest answer: {latest['answer']}",
            "Feedback they received: "
            + (latest["feedback"]["text"] if latest["feedback"] else "none"),
        ],
        "revealed": True,
        "extra_rules": [
            "This is a discussion of an assessment question the student "
            "must answer in their own words. Do not write or rewrite the "
            "student's answer, and do not state a model answer or list what "
            "a complete answer contains, even if asked directly. This "
            "overrides the rule about giving the full explanation after two "
            "attempts. Ask guiding questions, and point to a simulation to "
            f"revisit ({revisit}).",
        ],
    }, seed_message=seed, heading=f"Discuss question {number}")

layout.prev_next(PAGE_ID)
