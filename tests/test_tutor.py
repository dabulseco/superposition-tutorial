"""Checks for the tutor's instructions and text filters (tutor.py)."""

import tutor


def make_context(**changes):
    context = {
        "page_id": "t3b",
        "page_title": "Superposition vs. mixture",
        "controls": "sliders for theta and phi",
        "settings_lines": ["theta = 90 deg, phi = 0 deg", "Measurement axis: Along x"],
        "results_lines": ["Theory: P(+) superposition = 1.000"],
        "revealed": False,
        "hold_back": "the probabilities for the current axis",
    }
    context.update(changes)
    return context


# ---- build_system_prompt ----------------------------------------------------

def test_prompt_contains_every_settings_line():
    prompt = tutor.build_system_prompt(make_context())
    assert "theta = 90 deg, phi = 0 deg" in prompt
    assert "Measurement axis: Along x" in prompt


def test_prompt_withholds_results_until_revealed():
    prompt = tutor.build_system_prompt(make_context(revealed=False))
    assert "P(+) superposition = 1.000" not in prompt
    assert "has NOT run" in prompt
    assert "the probabilities for the current axis" in prompt


def test_prompt_includes_results_once_revealed():
    prompt = tutor.build_system_prompt(make_context(revealed=True))
    assert "P(+) superposition = 1.000" in prompt
    assert "has NOT run" not in prompt


def test_prompt_names_the_page_and_its_controls():
    prompt = tutor.build_system_prompt(make_context())
    assert "Superposition vs. mixture" in prompt
    assert "sliders for theta and phi" in prompt


def test_prompt_includes_extra_rules():
    prompt = tutor.build_system_prompt(
        make_context(extra_rules=["Do not write the student's answer."]))
    assert "Do not write the student's answer." in prompt


def test_prompt_keeps_the_next_questions_block():
    assert tutor.SUGGESTION_MARKER in tutor.build_system_prompt(make_context())


def test_prompt_includes_page_notes_and_shared_notes(tmp_path):
    (tmp_path / "shared.md").write_text("SHARED-NOTE-TEXT")
    (tmp_path / "t3b.md").write_text("PAGE-NOTE-TEXT")
    prompt = tutor.build_system_prompt(make_context(), notes_dir=tmp_path)
    assert "SHARED-NOTE-TEXT" in prompt and "PAGE-NOTE-TEXT" in prompt


def test_missing_notes_file_is_not_an_error(tmp_path):
    assert tutor.load_notes("no-such-page", notes_dir=tmp_path) == ""
    tutor.build_system_prompt(make_context(page_id="no-such-page"), notes_dir=tmp_path)


def test_shipped_notes_exist_for_the_go_deeper_page():
    notes = tutor.load_notes("t3b")
    assert "Bloch vector" in notes          # page notes
    assert "mixed state" in notes.lower()   # shared accuracy notes


def test_shipped_notes_never_name_newfos():
    for path in tutor.NOTES_DIR.glob("*.md"):
        assert "newfos" not in path.read_text().lower(), path.name


# ---- settings_text ----------------------------------------------------------

def test_settings_text_says_whether_the_experiment_ran():
    assert "not yet run" in tutor.settings_text(make_context(revealed=False))
    ran = tutor.settings_text(make_context(revealed=True))
    assert "P(+) superposition = 1.000" in ran and "theta = 90 deg" in ran


# ---- text filters -----------------------------------------------------------

def test_hide_thinking_removes_a_tag_split_across_pieces():
    pieces = ["Hello <th", "ink>secret</thi", "nk>world"]
    assert "".join(tutor.hide_thinking(pieces)) == "Hello world"


def test_split_suggestions_collects_questions_and_hides_them():
    suggestions = []
    pieces = ["The answer.\n\n**NEXT QUES", "TIONS:**\n- One?\n- Two?\n"]
    text = "".join(tutor.split_suggestions(pieces, suggestions))
    assert text == "The answer."
    assert suggestions == ["One?", "Two?"]


def test_split_suggestions_passes_text_through_without_a_marker():
    suggestions = []
    assert "".join(tutor.split_suggestions(["Just ", "text."], suggestions)) == "Just text."
    assert suggestions == []
