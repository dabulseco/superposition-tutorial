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


# ---- talking to Ollama (uses the stand-in server) ---------------------------

import pytest

HISTORY = [{"role": "user", "content": "Why?"}]


def test_list_models_keeps_ollama_order(ollama):
    assert tutor.list_models() == ["model-newest", "model-older"]


def test_list_models_reports_ollama_off():
    with pytest.raises(tutor.OllamaUnavailable):
        tutor.list_models()


def test_stream_answer_yields_the_whole_answer(ollama):
    assert "".join(tutor.stream_answer("m", "sys", HISTORY)) == "Hello there."


def test_stream_answer_sends_system_prompt_and_question(ollama):
    list(tutor.stream_answer("m", "SYSTEM-TEXT", HISTORY))
    sent = ollama.requests[-1]["messages"]
    assert sent[0] == {"role": "system", "content": "SYSTEM-TEXT"}
    assert sent[-1] == {"role": "user", "content": "Why?"}


def test_stream_answer_hides_thinking(ollama):
    ollama.stream_pieces = ["<think>private</think>", "Public."]
    assert "".join(tutor.stream_answer("m", "sys", HISTORY)) == "Public."


def test_error_reply_mentions_embedding_models(ollama):
    ollama.mode = "error500"
    with pytest.raises(tutor.OllamaUnavailable, match="embedding model"):
        list(tutor.stream_answer("m", "sys", HISTORY))


def test_dropped_connection_is_reported_not_silently_truncated(ollama):
    ollama.mode = "drop"
    with pytest.raises(tutor.OllamaUnavailable, match="before the answer was finished"):
        list(tutor.stream_answer("m", "sys", HISTORY))


# ---- one-shot calls used for feedback ---------------------------------------

def test_ask_text_returns_the_reply_without_thinking(ollama):
    ollama.replies = ["<think>hmm</think>Good start."]
    assert tutor.ask_text("m", "sys", "user text") == "Good start."
    sent = ollama.requests[-1]
    assert sent["stream"] is False
    assert sent["messages"][1] == {"role": "user", "content": "user text"}


def test_ask_json_sends_the_schema_and_parses_the_reply(ollama):
    ollama.replies = ['{"level": "developing"}']
    schema = {"type": "object"}
    assert tutor.ask_json("m", "sys", "user", schema) == {"level": "developing"}
    assert ollama.requests[-1]["format"] == schema


def test_ask_json_raises_value_error_for_non_json(ollama):
    ollama.replies = ["Sure! Here is my answer."]
    with pytest.raises(ValueError):
        tutor.ask_json("m", "sys", "user", {"type": "object"})


def test_one_shot_calls_report_ollama_off():
    with pytest.raises(tutor.OllamaUnavailable):
        tutor.ask_text("m", "sys", "user")


def test_prompt_can_draw_on_other_pages_notes(tmp_path):
    (tmp_path / "t4.md").write_text("PHIBIT-NOTE")
    (tmp_path / "t1.md").write_text("COIN-NOTE")
    prompt = tutor.build_system_prompt(
        make_context(page_id="tyu", notes_pages=["t4", "t1", "t4"]),
        notes_dir=tmp_path)
    assert prompt.count("PHIBIT-NOTE") == 1 and "COIN-NOTE" in prompt


def test_page_rules_are_marked_as_taking_priority():
    with_rules = tutor.build_system_prompt(
        make_context(extra_rules=["Do not reveal the node answer."]))
    heading = "RULES FOR THIS PAGE (these take priority over everything above)"
    assert heading in with_rules
    assert with_rules.index(heading) < with_rules.index("Do not reveal the node answer.")
    # They come last, after the notes, so they are the final word.
    assert with_rules.index("REFERENCE NOTES") < with_rules.index(heading)
    assert heading not in tutor.build_system_prompt(make_context())


def test_pending_prediction_rule_names_the_question_and_forbids_the_answer():
    rule = tutor.pending_prediction_rule("what happens to the still points")
    assert "what happens to the still points" in rule
    assert "do NOT state" in rule and "prediction" in rule


def test_normalize_math_turns_bracket_math_into_dollar_math():
    assert tutor.normalize_math(r"So \(u = 2a\) and \[x = 1\] ok") == \
        "So $u = 2a$ and $$x = 1$$ ok"
    assert tutor.normalize_math("plain $x$ text") == "plain $x$ text"


# ---- local or hosted, and which model is the default ------------------------

def _settings(monkeypatch, local_running, **env):
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(tutor, "_local_ollama_running", lambda: local_running)
    tutor.load_settings()


def test_a_key_on_a_laptop_with_ollama_running_stays_local(monkeypatch):
    _settings(monkeypatch, True, OLLAMA_API_KEY="k")
    assert not tutor.HOSTED
    assert tutor.OLLAMA_URL == "http://localhost:11434"


def test_a_key_with_no_local_ollama_means_hosted(monkeypatch):
    _settings(monkeypatch, False, OLLAMA_API_KEY="k")
    assert tutor.HOSTED
    assert tutor.OLLAMA_URL == "https://ollama.com"


def test_no_key_is_always_local(monkeypatch):
    _settings(monkeypatch, False)
    assert not tutor.HOSTED


def test_hosted_mode_can_be_forced_for_a_trial_run_on_a_laptop(monkeypatch):
    _settings(monkeypatch, True, OLLAMA_API_KEY="k", OLLAMA_MODE="hosted")
    assert tutor.HOSTED and tutor.OLLAMA_URL == "https://ollama.com"


def test_hosted_offers_the_whole_cloud_catalogue_by_default(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "k")
    tutor.load_settings()
    ollama.models = ["a", "gemma4:31b", "b", "c"]
    assert tutor.list_models() == ["a", "gemma4:31b", "b", "c"]


def test_hosted_list_can_still_be_narrowed_with_a_setting(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "k")
    monkeypatch.setenv("OLLAMA_MODELS", "c, a")
    tutor.load_settings()
    ollama.models = ["a", "gemma4:31b", "b", "c"]
    assert tutor.list_models() == ["c", "a"]


def test_default_model_is_gemma4_31b_cloud_locally():
    models = ["gemma4:26b", "gemma4:31b-cloud", "gpt-oss:20b"]
    assert tutor.default_model(models) == "gemma4:31b-cloud"


def test_default_model_is_the_cloud_gemma_when_hosted(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "k")
    tutor.load_settings()
    assert tutor.default_model(["gpt-oss:20b", "gemma4:31b"]) == "gemma4:31b"


def test_default_falls_back_to_the_first_model_if_gemma_is_missing():
    assert tutor.default_model(["model-newest", "model-older"]) == "model-newest"


def test_default_model_can_be_set(monkeypatch):
    monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "gpt-oss:20b")
    tutor.load_settings()
    assert tutor.default_model(["gemma4:31b-cloud", "gpt-oss:20b"]) == "gpt-oss:20b"
