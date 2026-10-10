"""Checks on the text files in content/."""

from pathlib import Path

import yaml

from components import layout

ROOT = Path(__file__).parent.parent
PAGES = yaml.safe_load((ROOT / "content" / "pages.yaml").read_text())


def test_every_page_has_a_title_and_intro():
    for page_id, _, _ in layout.PAGES:
        assert PAGES[page_id]["title"] and PAGES[page_id]["intro"], page_id


def test_page_text_avoids_the_two_reworded_phrases():
    text = yaml.safe_dump(PAGES).lower()
    assert "mixed state" not in text
    assert "experiencing a mix" not in text


def test_no_content_file_names_newfos():
    for path in (ROOT / "content").rglob("*"):
        if path.is_file():
            assert "newfos" not in path.read_text().lower(), path.name


def test_every_page_file_exists():
    for _, file, _ in layout.PAGES:
        assert (ROOT / file).is_file(), file


# ---- questions.yaml ---------------------------------------------------------

import pytest

import feedback

VALID_PAGES = set(layout.PAGE_FILES)
DRAFT = ROOT / "content" / "questions.rubric-draft.yaml"

SPELMAN_QUESTIONS = [
    "What is a superposition state?",
    "How does a physical phi-bit represented by a spring-mass chain "
    "demonstrate a superposition state?",
    "What are the differences and similarities between a qubit and a coin "
    "resting on a table?",
]


def test_shipped_questions_keep_the_spelman_wording_exactly():
    questions = feedback.load_questions(valid_pages=VALID_PAGES)
    assert [q["text"] for q in questions] == SPELMAN_QUESTIONS
    assert [q["id"] for q in questions] == ["q1", "q2", "q3"]


def test_shipped_questions_have_no_rubric_yet():
    for question in feedback.load_questions(valid_pages=VALID_PAGES):
        assert not feedback.has_rubric(question)
        assert question["revisit"], "every question needs a revisit link"


def test_draft_rubric_loads_and_covers_all_three_questions():
    questions = feedback.load_questions(DRAFT, valid_pages=VALID_PAGES)
    assert [q["text"] for q in questions] == SPELMAN_QUESTIONS
    assert all(feedback.has_rubric(q) for q in questions)


def _write(tmp_path, body):
    path = tmp_path / "questions.yaml"
    path.write_text(body)
    return path


GOOD = """
questions:
  - id: q1
    text: "A question?"
    revisit: [{label: "Topic 1", page: t1}]
    key_ideas: [{id: q1.k1, text: "an idea"}]
    misconceptions: []
"""


def test_a_hand_written_rubric_loads(tmp_path):
    questions = feedback.load_questions(_write(tmp_path, GOOD), VALID_PAGES)
    assert feedback.has_rubric(questions[0])
    assert questions[0]["key_ideas"][0]["advanced"] is False


@pytest.mark.parametrize("change, problem", [
    (("id: q1\n    text", "id: q1\n    wording"), "text"),
    (('text: "A question?"', 'text: ""'), "text"),
    (("{id: q1.k1, text: \"an idea\"}", "{text: \"an idea\"}"), "id"),
    (("{id: q1.k1, text: \"an idea\"}",
      "{id: q1.k1, text: \"an idea\"}, {id: q1.k1, text: \"again\"}"), "q1.k1"),
    (("page: t1", "page: t9"), "t9"),
    (("revisit: [{label: \"Topic 1\", page: t1}]", "revisit: []"), "revisit"),
    (("questions:", "items:"), "questions"),
])
def test_mistakes_in_the_file_are_named(tmp_path, change, problem):
    path = _write(tmp_path, GOOD.replace(*change))
    with pytest.raises(feedback.ContentError) as error:
        feedback.load_questions(path, VALID_PAGES)
    assert "questions.yaml" in str(error.value)
    assert problem in str(error.value)


def test_duplicate_question_ids_are_named(tmp_path):
    second = GOOD.split("questions:")[1].replace("q1.k1", "q1.k2")
    with pytest.raises(feedback.ContentError, match="q1"):
        feedback.load_questions(_write(tmp_path, GOOD + second), VALID_PAGES)


def test_broken_yaml_is_reported_not_crashed(tmp_path):
    path = _write(tmp_path, "questions:\n  - id: q1\n   text: bad indent\n")
    with pytest.raises(feedback.ContentError, match="questions.yaml"):
        feedback.load_questions(path, VALID_PAGES)


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(feedback.ContentError, match="nowhere.yaml"):
        feedback.load_questions(tmp_path / "nowhere.yaml", VALID_PAGES)
