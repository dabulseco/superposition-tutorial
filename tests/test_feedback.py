"""Checks for Test Your Understanding feedback (feedback.py)."""

import json

import pytest

import feedback
import tutor

NO_RUBRIC = {
    "id": "q1", "text": "What is a superposition state?",
    "revisit": [{"label": "Topic 3: the probability slider", "page": "t3"}],
    "key_ideas": [], "misconceptions": [],
}
RUBRIC = dict(NO_RUBRIC, key_ideas=[
    {"id": "q1.k1", "text": "A combination of two basic states at once.",
     "advanced": False},
    {"id": "q1.k2", "text": "Measuring gives just one of the basic states.",
     "advanced": False},
], misconceptions=[
    {"id": "M-mixture",
     "text": "It is secretly one state and we just don't know which."},
])
ANSWER = "It is when a thing is in two states at once."


def check(k1=("present", "two states at once"), k2=("absent", ""),
          misconceptions=(), level="developing", **extra):
    """A rubric-check reply as the model would send it."""
    return json.dumps({
        "question_id": "q1",
        "key_ideas": [
            {"id": "q1.k1", "status": k1[0], "evidence": k1[1]},
            {"id": "q1.k2", "status": k2[0], "evidence": k2[1]},
        ],
        "misconceptions": [{"id": m[0], "evidence": m[1]} for m in misconceptions],
        "level": level, **extra})


GOOD_TEXT = ('You wrote "two states at once", which is the heart of it. '
             "What do you actually see when you measure? Try the slider.")


def statuses(result):
    return {idea["id"]: idea["status"] for idea in result["rubric"]["key_ideas"]}


# ---- no rubric: guided mode -------------------------------------------------

def test_without_a_rubric_feedback_takes_one_call(ollama):
    ollama.replies = [GOOD_TEXT]
    result = feedback.give_feedback("m", NO_RUBRIC, ANSWER)
    assert result == {"text": GOOD_TEXT, "mode": "guided", "rubric": None,
                      "flagged": False}
    assert len(ollama.requests) == 1


def test_guided_prompt_carries_the_question_answer_and_rules(ollama):
    ollama.replies = [GOOD_TEXT]
    feedback.give_feedback("m", NO_RUBRIC, ANSWER)
    system, user = (m["content"] for m in ollama.requests[0]["messages"])
    assert NO_RUBRIC["text"] in user and ANSWER in user
    assert "guiding question" in system
    assert "Never" in system and "Topic 3: the probability slider" in system


def test_empty_reply_falls_back_to_the_neutral_message(ollama):
    ollama.replies = ["   "]
    result = feedback.give_feedback("m", NO_RUBRIC, ANSWER)
    assert result["mode"] == "fallback" and result["flagged"]
    assert result["text"] == feedback.FALLBACK_TEXT


# ---- with a rubric ----------------------------------------------------------

def test_with_a_rubric_feedback_takes_two_calls(ollama):
    ollama.replies = [check(), GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "rubric" and not result["flagged"]
    assert result["text"] == GOOD_TEXT
    assert statuses(result) == {"q1.k1": "present", "q1.k2": "absent"}
    assert result["rubric"]["level"] == "developing"
    assert len(ollama.requests) == 2
    assert "format" in ollama.requests[0]          # structured output asked for


def test_evidence_match_ignores_case_and_spacing(ollama):
    ollama.replies = [check(k1=("present", "Two  States\nAT once")), GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert statuses(result)["q1.k1"] == "present"
    assert len(ollama.requests) == 2


def test_invented_evidence_marks_the_idea_absent_and_rechecks_once(ollama):
    invented = check(k2=("present", "the wave function collapses"))
    ollama.replies = [invented, check(), GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert statuses(result)["q1.k2"] == "absent"
    assert len(ollama.requests) == 3


def test_evidence_invented_twice_is_still_not_credited(ollama):
    invented = check(k2=("present", "the wave function collapses"))
    ollama.replies = [invented, invented, GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "rubric"
    assert statuses(result) == {"q1.k1": "present", "q1.k2": "absent"}
    assert len(ollama.requests) == 3               # one recheck only


def test_unknown_ids_are_dropped_and_missing_ideas_count_as_absent(ollama):
    reply = json.dumps({
        "question_id": "q1", "level": "beginning",
        "key_ideas": [{"id": "q9.k7", "status": "present",
                       "evidence": "two states at once"}],
        "misconceptions": [{"id": "M-made-up", "evidence": "two states"}]})
    ollama.replies = [reply, GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert statuses(result) == {"q1.k1": "absent", "q1.k2": "absent"}
    assert result["rubric"]["misconceptions"] == []


def test_misconception_needs_evidence_from_the_answer(ollama):
    answer = "It is secretly heads or tails, we just don't know."
    real = check(k1=("absent", ""),
                 misconceptions=[("M-mixture", "secretly heads or tails")])
    ollama.replies = [real, GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, answer)
    assert [m["id"] for m in result["rubric"]["misconceptions"]] == ["M-mixture"]


def test_invalid_level_is_rejected_then_falls_back(ollama):
    ollama.replies = [check(level="excellent"), check(level="A+")]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "fallback" and result["flagged"]
    assert result["rubric"] is None
    assert len(ollama.requests) == 2


def test_non_json_reply_gets_one_retry_then_fallback(ollama):
    ollama.replies = ["I think the answer is good.", "{not json"]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "fallback" and result["flagged"]
    assert result["text"] == feedback.FALLBACK_TEXT
    assert len(ollama.requests) == 2


def test_non_json_reply_recovers_on_the_retry(ollama):
    ollama.replies = ["oops", check(), GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "rubric"


def test_wrong_shape_json_is_treated_like_broken_json(ollama):
    ollama.replies = ['["a list"]', '{"key_ideas": "nope", "level": "developing"}']
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "fallback"


GIVEAWAY = ("Good try. Remember that measuring gives just one of the basic "
            "states. Revisit the slider.")


def test_feedback_that_states_a_missing_idea_is_rewritten_once(ollama):
    ollama.replies = [check(), GIVEAWAY, GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "rubric" and result["text"] == GOOD_TEXT
    assert len(ollama.requests) == 3


def test_feedback_that_keeps_giving_the_answer_away_falls_back(ollama):
    ollama.replies = [check(), GIVEAWAY, GIVEAWAY]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    assert result["mode"] == "fallback" and result["flagged"]
    assert result["text"] == feedback.FALLBACK_TEXT
    assert result["rubric"] is not None            # the check itself was fine


def test_quoting_an_idea_the_student_already_has_is_allowed(ollama):
    both = check(k2=("present", "in two states"))
    echo = ("Yes: a combination of two basic states at once, as you said. "
            "What sets the chance of each result?")
    ollama.replies = [both, echo]
    assert feedback.give_feedback("m", RUBRIC, ANSWER)["mode"] == "rubric"


def test_feedback_never_shows_the_level(ollama):
    ollama.replies = [check(), GOOD_TEXT]
    feedback.give_feedback("m", RUBRIC, ANSWER)
    writer_system = ollama.requests[1]["messages"][0]["content"]
    assert "score" in writer_system.lower()        # told not to give one


def test_ollama_off_is_passed_up_to_the_page():
    with pytest.raises(tutor.OllamaUnavailable):
        feedback.give_feedback("m", NO_RUBRIC, ANSWER)
    with pytest.raises(tutor.OllamaUnavailable):
        feedback.give_feedback("m", RUBRIC, ANSWER)


# ---- hardening from review --------------------------------------------------

from pathlib import Path

DRAFT = {q["id"]: q for q in feedback.load_questions(
    Path(feedback.QUESTIONS_FILE).with_name("questions.rubric-draft.yaml"))}


def all_absent(question):
    return {"key_ideas": [{"id": i["id"], "status": "absent", "evidence": ""}
                          for i in question["key_ideas"]]}


def test_giveaway_check_catches_one_half_of_a_two_part_idea():
    text = "Equal amounts of the two waves make a standing wave."
    assert feedback.copies_rubric(text, DRAFT["q2"], all_absent(DRAFT["q2"]))


def test_giveaway_check_ignores_words_from_the_question_and_revisit_labels():
    text = ("You noted that both have two outcomes. What can you say about "
            "the coin before anyone looks at it? Revisit Topic 1: Bits & "
            "Superposition, then Topic 3: Electrons & Qubits.")
    assert not feedback.copies_rubric(text, DRAFT["q3"], all_absent(DRAFT["q3"]))


@pytest.mark.parametrize("evidence", ["e", "is", "at once", "tates at onc"])
def test_evidence_must_be_whole_words_and_more_than_a_scrap(ollama, evidence):
    # "at once" is two real words from the answer, so it alone is accepted.
    ollama.replies = [check(k1=("present", evidence)), check(k1=("absent", "")),
                      GOOD_TEXT]
    result = feedback.give_feedback("m", RUBRIC, ANSWER)
    expected = "present" if evidence == "at once" else "absent"
    assert statuses(result)["q1.k1"] == expected
