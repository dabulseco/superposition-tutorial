"""Checks that each page runs and behaves, using Streamlit's test runner."""

from streamlit.testing.v1 import AppTest

from components import layout


APP = str(layout.ROOT / "app.py")


def run_page(page_id, **session):
    """Run one page on its own (no sidebar, so the tutor is off)."""
    at = AppTest.from_file(str(layout.ROOT / layout.PAGE_FILES[page_id]),
                           default_timeout=30)
    for key, value in session.items():
        at.session_state[key] = value
    return at.run()


def texts(elements):
    return " ".join(str(e.value) for e in elements)


def all_text(at):
    return " ".join([texts(at.markdown), texts(at.caption), texts(at.info),
                     texts(at.success), texts(at.warning), texts(at.title),
                     texts(at.subheader)])


# ---- the app shell ----------------------------------------------------------

def test_app_opens_on_home_with_ollama_off():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value == "Superposition State Primer"


def test_footer_credits_spelman_and_ifi_only():
    at = AppTest.from_file(APP, default_timeout=30).run()
    footer = at.caption[-1].value
    assert "Spelman College" in footer
    assert "Institute for Future Intelligence" in footer
    assert "nothing you type is stored" in footer
    assert "newfos" not in all_text(at).lower()


def test_footer_wording_changes_when_hosted(monkeypatch, ollama):
    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "sent to Ollama's cloud service" in at.caption[-1].value


def test_sidebar_shows_progress():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "Questions answered: 0 of 3" in texts(at.sidebar.markdown)


def test_every_page_opens_with_ollama_off():
    # The test runner opens pages on their own, outside app.py. The footer
    # is drawn by app.py after whichever page runs, so it is checked above.
    for page_id, _, _ in layout.PAGES:
        at = run_page(page_id)
        assert not at.exception, page_id
        assert at.title[0].value == layout.page_text(page_id)["title"]


# ---- Go deeper: superposition vs. mixture -----------------------------------

def test_t3b_is_locked_until_a_prediction_is_made():
    at = run_page("t3b")
    assert not at.exception
    assert "Make a prediction" in texts(at.info)
    assert "The tutor is off" in texts(at.info)


def test_t3b_shows_theory_numbers_after_running():
    at = run_page("t3b")
    at.radio(key="t3b_axis").set_value("Along x").run()
    at.radio(key="t3b_prediction").set_value("different results").run()
    at.button(key="t3b_run").click().run()
    values = {m.label: m.value for m in at.metric}
    assert values["Superposition: P(+) theory"] == "1.000"
    assert values["Mixture: P(+) theory"] == "0.500"
    assert "Your prediction matches" in texts(at.success)
    assert at.session_state["journey"][-1]["type"] == "run"


def test_t3b_relocks_when_theta_changes_after_a_run():
    at = run_page("t3b")
    at.radio(key="t3b_prediction").set_value("the same results").run()
    at.button(key="t3b_run").click().run()
    assert len(at.metric) == 2
    at.slider(key="t3b_theta").set_value(60).run()
    assert len(at.metric) == 0
    assert at.radio(key="t3b_prediction").value == "Choose one"
    assert "Settings changed" in texts(at.info)


# ---- Topic 1: Bits & Superposition ------------------------------------------

def test_t1_classical_bit_reports_the_set_state():
    at = run_page("t1")
    at.button(key="t1_measure_bit").click().run()
    assert "It is exactly ON." in texts(at.success)
    at.toggle(key="t1_switch_on").set_value(False).run()
    at.button(key="t1_measure_bit").click().run()
    assert "It is exactly OFF." in texts(at.success)


def test_t1_switch_measured_ten_times_always_reads_the_same():
    at = run_page("t1")
    at.number_input(key="t1_switch10_prediction").set_value(10).run()
    at.button(key="t1_switch10_run").click().run()
    assert "ON 10 times out of 10" in all_text(at)
    assert "Your prediction matches" in texts(at.success)


def test_t1_coin_snaps_then_resets():
    at = run_page("t1")
    assert "spinning in a blur" in all_text(at)
    assert at.button(key="t1_coin_btn").label == "Measure Coin (Slap it down!)"
    at.button(key="t1_coin_btn").click().run()
    assert at.session_state["t1_coin"] in ("HEADS", "TAILS")
    assert f"It snapped to: {at.session_state['t1_coin']}" in all_text(at)
    assert at.button(key="t1_coin_btn").label == "Reset (Spin Again)"
    at.button(key="t1_coin_btn").click().run()
    assert at.session_state["t1_coin"] is None
    assert "spinning in a blur" in all_text(at)


def test_t1_hundred_coins_need_a_prediction_and_add_to_the_tally():
    at = run_page("t1")
    assert at.session_state["t1_tally"] == [0, 0]
    at.number_input(key="t1_coin100_prediction").set_value(50).run()
    at.button(key="t1_coin100_run").click().run()
    assert sum(at.session_state["t1_tally"]) == 100
    at.button(key="t1_coin100_run").click().run()
    assert sum(at.session_state["t1_tally"]) == 200
    runs = [e for e in at.session_state["journey"] if e["type"] == "measure_100_coins"]
    assert len(runs) == 2 and runs[0]["details"]["prediction"] == 50


def test_t1_explains_where_the_coin_analogy_breaks():
    at = run_page("t1")
    assert at.expander[0].label == "Where the analogy breaks"
    assert "classical mixture" in texts(at.expander[0].markdown)


def test_t1_works_with_ollama_off():
    at = run_page("t1")
    assert not at.exception
    assert "The tutor is off" in texts(at.info)


# ---- Topic 2: Coupled Oscillators -------------------------------------------

def metrics(at):
    return {m.label: m.value for m in at.metric}


def test_t2_starts_at_right_40_for_both_weights():
    at = run_page("t2")
    assert not at.exception
    assert at.slider(key="t2_x1").value == 40 and at.slider(key="t2_x2").value == 40
    assert "Right 40" in all_text(at)


def test_t2_pattern_1_preset_plays_pattern_1_only():
    at = run_page("t2")
    at.slider(key="t2_x1").set_value(-10).run()
    at.button(key="t2_preset_p1").click().run()
    assert (at.slider(key="t2_x1").value, at.slider(key="t2_x2").value) == (40, 40)
    assert metrics(at)["Pattern 1 amplitude"] == "40"
    assert metrics(at)["Pattern 2 amplitude"] == "0"


def test_t2_pattern_2_preset_plays_pattern_2_only():
    at = run_page("t2")
    at.button(key="t2_preset_p2").click().run()
    assert (at.slider(key="t2_x1").value, at.slider(key="t2_x2").value) == (40, -40)
    assert metrics(at)["Pattern 1 amplitude"] == "0"
    assert metrics(at)["Pattern 2 amplitude"] == "40"


def test_t2_random_preset_always_mixes_both_patterns():
    at = run_page("t2")
    for _ in range(5):
        at.button(key="t2_preset_random").click().run()
        assert abs(at.slider(key="t2_x1").value) != abs(at.slider(key="t2_x2").value)
        assert metrics(at)["Pattern 1 amplitude"] != "0"
        assert metrics(at)["Pattern 2 amplitude"] != "0"


def test_t2_prediction_sets_up_the_one_sided_pull():
    at = run_page("t2")
    at.radio(key="t2_predict_prediction").set_value("Both, in equal amounts").run()
    at.button(key="t2_predict_run").click().run()
    assert (at.slider(key="t2_x1").value, at.slider(key="t2_x2").value) == (40, 0)
    assert metrics(at)["Pattern 1 amplitude"] == "20"
    assert metrics(at)["Pattern 2 amplitude"] == "20"
    assert "Your prediction matches" in texts(at.success)


def test_t2_spectrum_peaks_agree_with_the_pattern_amplitudes():
    at = run_page("t2")
    at.slider(key="t2_x2").set_value(-10).run()      # x1 = 40, x2 = -10
    assert metrics(at)["Pattern 1 amplitude"] == "15"
    assert metrics(at)["Pattern 2 amplitude"] == "25"
    assert "peaks of height 15.0 and 25.0" in all_text(at)


def test_t2_both_weights_at_center_does_not_break():
    at = run_page("t2")
    at.slider(key="t2_x1").set_value(0).run()
    at.slider(key="t2_x2").set_value(0).run()
    assert not at.exception
    assert "No state yet" in all_text(at)


# ---- Topic 3: Electrons & Qubits --------------------------------------------

def test_t3_starts_at_5050_with_the_arrow_on_the_equator():
    at = run_page("t3")
    assert not at.exception
    assert at.slider(key="t3_p").value == 50
    assert "50% UP / 50% DOWN" in all_text(at)
    assert "tilted 90°" in all_text(at)
    assert at.session_state["t3_outcomes"] == []


def test_t3_measure_once_snaps_and_counts_one_result():
    at = run_page("t3")
    at.button(key="t3_measure1").click().run()
    assert at.session_state["t3_snapped"] in ("UP", "DOWN")
    assert f"It snapped to: Spin {at.session_state['t3_snapped']}" in all_text(at)
    assert len(at.session_state["t3_outcomes"]) == 1


def test_t3_measuring_the_same_qubit_again_repeats_the_result():
    at = run_page("t3")
    at.button(key="t3_measure1").click().run()
    first = at.session_state["t3_snapped"]
    for _ in range(5):
        at.button(key="t3_again").click().run()
        assert at.session_state["t3_snapped"] == first
        assert f"Same result: {first}" in all_text(at)
    assert len(at.session_state["t3_outcomes"]) == 1    # not new data


def test_t3_measure_100_needs_a_prediction_and_adds_100_results():
    at = run_page("t3")
    at.number_input(key="t3_predict_prediction").set_value(50).run()
    at.button(key="t3_predict_run").click().run()
    assert len(at.session_state["t3_outcomes"]) == 100
    assert at.session_state["t3_snapped"] is None       # arrow reset
    assert "Ran 100 measurements!" in all_text(at)
    at.button(key="t3_predict_run").click().run()
    assert len(at.session_state["t3_outcomes"]) == 200
    at.button(key="t3_clear").click().run()
    assert at.session_state["t3_outcomes"] == []


def test_t3_certain_state_gives_only_up():
    at = run_page("t3")
    at.slider(key="t3_p").set_value(100).run()
    assert "tilted 0°" in all_text(at)
    at.number_input(key="t3_predict_prediction").set_value(100).run()
    at.button(key="t3_predict_run").click().run()
    assert sum(at.session_state["t3_outcomes"]) == 100
    assert "Your prediction matches" in texts(at.success)


def test_t3_changing_the_mix_clears_old_data_and_relocks():
    at = run_page("t3")
    at.number_input(key="t3_predict_prediction").set_value(50).run()
    at.button(key="t3_predict_run").click().run()
    at.slider(key="t3_p").set_value(70).run()
    assert at.session_state["t3_outcomes"] == []
    assert at.number_input(key="t3_predict_prediction").value is None


# ---- Topic 4: Phi-Bit Systems -----------------------------------------------

def test_t4_starts_in_pure_state_0():
    at = run_page("t4")
    assert not at.exception
    assert at.slider(key="t4_left").value == 100 and at.slider(key="t4_right").value == 0
    assert "Pure State 0 (Only Left)" in texts(at.info)


def test_t4_presets_give_the_matching_status():
    at = run_page("t4")
    at.button(key="t4_preset_right").click().run()
    assert "Pure State 1 (Only Right)" in texts(at.info)
    at.button(key="t4_preset_super").click().run()
    assert (at.slider(key="t4_left").value, at.slider(key="t4_right").value) == (100, 100)
    assert "50/50 Superposition! (Standing Wave)" in texts(at.info)
    at.button(key="t4_preset_left").click().run()
    assert "Pure State 0 (Only Left)" in texts(at.info)


def test_t4_sliders_are_labeled_as_amplitudes_with_power_readouts():
    at = run_page("t4")
    assert at.slider(key="t4_left").label == "LEFT Wave Amplitude"
    assert at.slider(key="t4_right").label == "RIGHT Wave Amplitude"
    at.slider(key="t4_left").set_value(80).run()
    at.slider(key="t4_right").set_value(60).run()
    values = metrics(at)
    assert values["LEFT wave power"] == "0.64"
    assert values["RIGHT wave power"] == "0.36"
    assert values["Share of State 1"] == "36%"
    assert "Superposition! (Uneven Mix)" in texts(at.info)


def test_t4_no_waves_does_not_break():
    at = run_page("t4")
    at.slider(key="t4_left").set_value(0).run()
    assert not at.exception
    assert "You turned off all waves!" in texts(at.info)
    assert metrics(at)["Share of State 1"] == "—"
    assert "No state yet" in all_text(at)


def test_t4_phase_slides_the_still_points():
    at = run_page("t4")
    at.button(key="t4_preset_super").click().run()
    assert "have not moved" in all_text(at)
    at.slider(key="t4_delta").set_value(60).run()
    assert "moved 0.67 weight spacings" in all_text(at)
    assert "50/50 Superposition! (Standing Wave)" in texts(at.info)


def test_t4_phase_prediction_sets_up_a_5050_mix():
    at = run_page("t4")
    at.radio(key="t4_predict_prediction").set_value(
        "They slide along the chain; the wave stays standing").run()
    at.button(key="t4_predict_run").click().run()
    assert (at.slider(key="t4_left").value, at.slider(key="t4_right").value) == (100, 100)
    assert "Your prediction matches" in texts(at.success)


def test_t4_opens_on_the_preset_a_revisit_link_asks_for():
    at = run_page("t4", arrive_t4="superposition")
    assert (at.slider(key="t4_left").value, at.slider(key="t4_right").value) == (100, 100)


def test_t4_real_chain_has_a_lowest_frequency():
    at = run_page("t4")
    at.toggle(key="t4_real").set_value(True).run()
    assert "No traveling wave at this frequency" not in texts(at.warning)
    at.slider(key="t4_freq").set_value(0.5).run()
    assert not at.exception
    assert "No traveling wave at this frequency" in texts(at.warning)


# ---- Test Your Understanding ------------------------------------------------

import feedback
import tutor

Q1 = "What is a superposition state?"
MY_ANSWER = "It is when a thing is in two states at once."
REPLY = 'You wrote "two states at once". What happens when you measure?'


def tyu(model="m"):
    """The page with a tutor model already picked (as the sidebar would)."""
    return run_page("tyu", tutor_model=model)


def submit(at, qid, answer):
    at.text_area(key=f"tyu_draft_{qid}").set_value(answer).run()
    at.button(key=f"tyu_submit_{qid}").click().run()
    return at


def test_tyu_shows_the_three_spelman_questions_with_ollama_off():
    at = run_page("tyu")
    assert not at.exception
    page = all_text(at)
    for question in feedback.load_questions():
        assert question["text"] in page


def test_tyu_submit_saves_attempt_one_with_feedback(ollama):
    ollama.replies = [REPLY]
    at = submit(tyu(), "q1", MY_ANSWER)
    attempts = at.session_state["tyu_attempts"]["q1"]
    assert len(attempts) == 1
    assert attempts[0]["number"] == 1 and attempts[0]["answer"] == MY_ANSWER
    assert attempts[0]["feedback"]["text"] == REPLY
    assert REPLY in all_text(at)
    event = at.session_state["journey"][-1]
    assert event["type"] == "tyu_submit"
    assert event["details"]["question_id"] == "q1"
    assert event["details"]["feedback"] == REPLY


def test_tyu_second_submit_adds_attempt_two_and_keeps_attempt_one(ollama):
    ollama.replies = [REPLY, "Second feedback."]
    at = submit(tyu(), "q1", MY_ANSWER)
    at = submit(at, "q1", MY_ANSWER + " Measuring gives one result.")
    attempts = at.session_state["tyu_attempts"]["q1"]
    assert [a["number"] for a in attempts] == [1, 2]
    assert attempts[0]["answer"] == MY_ANSWER
    assert attempts[0]["feedback"]["text"] == REPLY
    assert attempts[1]["feedback"]["text"] == "Second feedback."


def test_tyu_empty_or_blank_answer_is_not_submitted(ollama):
    at = tyu()
    at.button(key="tyu_submit_q1").click().run()
    at = submit(at, "q1", "   \n  ")
    assert at.session_state["tyu_attempts"].get("q1", []) == []
    assert "Write an answer" in texts(at.warning)
    assert ollama.requests == []


def test_tyu_answers_are_capped_at_4000_characters():
    at = run_page("tyu")
    assert at.text_area(key="tyu_draft_q1").proto.max_chars == 4000


def test_tyu_confidence_is_saved_with_the_attempt(ollama):
    ollama.replies = [REPLY]
    at = tyu()
    at.select_slider(key="tyu_confidence_q1").set_value("4").run()
    at = submit(at, "q1", MY_ANSWER)
    assert at.session_state["tyu_attempts"]["q1"][0]["confidence"] == 4


def test_tyu_saves_the_answer_when_the_tutor_is_off():
    at = submit(run_page("tyu"), "q1", MY_ANSWER)      # no model picked
    attempts = at.session_state["tyu_attempts"]["q1"]
    assert len(attempts) == 1 and attempts[0]["feedback"] is None
    assert "Your answer is saved. Feedback is unavailable right now." in all_text(at)


def test_tyu_saves_the_answer_when_ollama_fails_mid_feedback():
    at = submit(tyu(), "q1", MY_ANSWER)      # model picked, but Ollama is dead
    assert not at.exception
    attempts = at.session_state["tyu_attempts"]["q1"]
    assert len(attempts) == 1 and attempts[0]["feedback"] is None
    assert "Your answer is saved. Feedback is unavailable right now." in all_text(at)


def test_tyu_questions_keep_separate_drafts_and_attempts(ollama):
    ollama.replies = [REPLY]
    at = tyu()
    at.text_area(key="tyu_draft_q2").set_value("my q2 draft").run()
    at = submit(at, "q1", MY_ANSWER)
    assert at.text_area(key="tyu_draft_q2").value == "my q2 draft"
    assert "q2" not in at.session_state["tyu_attempts"]


def test_tyu_discuss_seeds_the_chat_and_forbids_writing_the_answer(ollama):
    ollama.replies = [REPLY]
    at = submit(tyu(), "q1", MY_ANSWER)
    at.button(key="tyu_discuss_q1").click().run()
    chat = at.session_state["chat_tyu_q1"]
    assert Q1 in chat[0]["content"] and MY_ANSWER in chat[0]["content"]
    assert chat[1]["role"] == "assistant"
    system = ollama.requests[-1]["messages"][0]["content"]
    assert "Do not write or rewrite the student's answer" in system


def test_tyu_warns_about_personal_information_when_hosted(monkeypatch, ollama):
    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")
    tutor.load_settings()
    at = tyu()
    assert "don't type personal information" in texts(at.caption)


def test_tyu_reports_a_broken_questions_file(monkeypatch, tmp_path):
    bad = tmp_path / "questions.yaml"
    bad.write_text("questions:\n  - id: q1\n")
    monkeypatch.setattr(feedback, "QUESTIONS_FILE", bad)
    at = run_page("tyu")
    assert not at.exception
    assert "Problem in questions.yaml" in texts(at.error)


# ---- Quick checks -----------------------------------------------------------

import pytest

QUICK = [("t1", "qc-t1-1", "a classical bit in a definite state", "50% heads"),
         ("t2", "qc-t2-2", "both, equally", "neither"),
         ("t3", "qc-t3-2", "UP", "50/50"),
         ("t4", "qc-t4-1", "a standing wave", "no wave")]


@pytest.mark.parametrize("page, item, right, wrong", QUICK)
def test_quick_check_gives_feedback_for_wrong_and_right_answers(page, item, right, wrong):
    at = run_page(page)
    assert "Quick check" in texts(at.subheader)
    at.radio(key=f"quick_{item}").set_value(wrong).run()
    at.button(key=f"quick_check_{item}").click().run()
    assert not at.exception
    assert "Not quite" in texts(at.warning)
    assert right not in texts(at.warning)           # no answer given away
    at.radio(key=f"quick_{item}").set_value(right).run()
    at.button(key=f"quick_check_{item}").click().run()
    assert "Correct" in texts(at.success)
    checks = [e for e in at.session_state["journey"] if e["type"] == "quick_check"]
    assert [c["details"]["correct"] for c in checks] == [False, True]
    assert checks[0]["details"]["item_id"] == item


def test_quick_check_needs_a_choice_first():
    at = run_page("t1")
    at.button(key="quick_check_qc-t1-1").click().run()
    assert "Choose an answer first" in texts(at.info)
    assert not [e for e in at.session_state["journey"] if e["type"] == "quick_check"]


# ---- results and messages must belong to what is on screen ------------------

def test_t3_message_follows_the_slider_after_a_run():
    at = run_page("t3")
    at.number_input(key="t3_predict_prediction").set_value(50).run()
    at.button(key="t3_predict_run").click().run()
    at.slider(key="t3_p").set_value(60).run()
    assert "Ran 100 measurements!" not in all_text(at)
    assert "Prepared in a 60% UP mix." in texts(at.info)


def test_t3_clear_data_also_clears_the_last_run_summary():
    at = run_page("t3")
    at.number_input(key="t3_predict_prediction").set_value(50).run()
    at.button(key="t3_predict_run").click().run()
    assert "This run:" in all_text(at)
    at.button(key="t3_clear").click().run()
    assert "This run:" not in all_text(at)
    assert "Ran 100 measurements!" not in all_text(at)


def test_t3_prediction_cannot_be_changed_to_match_the_result():
    at = run_page("t3")
    at.number_input(key="t3_predict_prediction").set_value(0).run()
    at.button(key="t3_predict_run").click().run()
    assert at.number_input(key="t3_predict_prediction").disabled


def test_t4_5050_message_only_shows_while_the_mix_is_5050():
    at = run_page("t4")
    at.radio(key="t4_predict_prediction").set_value(
        "They slide along the chain; the wave stays standing").run()
    at.button(key="t4_predict_run").click().run()
    assert "The mix is now 50/50" in all_text(at)
    at.slider(key="t4_right").set_value(0).run()
    assert "The mix is now 50/50" not in all_text(at)


def test_t2_prediction_message_notes_when_the_weights_have_moved():
    at = run_page("t2")
    at.radio(key="t2_predict_prediction").set_value("Pattern 1 only").run()
    at.button(key="t2_predict_run").click().run()
    assert "Right 40 and Center 0" in texts(at.warning)
    at.slider(key="t2_x2").set_value(30).run()
    assert "Right 40 and Center 0" not in texts(at.warning)
    assert "You have moved the weights" in all_text(at)


def test_t4_out_of_band_does_not_also_claim_a_standing_wave():
    at = run_page("t4")
    at.button(key="t4_preset_super").click().run()
    at.toggle(key="t4_real").set_value(True).run()
    at.slider(key="t4_freq").set_value(0.5).run()
    assert "Standing Wave" not in texts(at.info)
    assert "No traveling wave at this frequency" in texts(at.warning)


def test_no_page_shows_a_streamlit_state_warning_on_first_load():
    for page_id in ("t1", "t2", "t3", "t3b", "t4", "tyu"):
        at = run_page(page_id)
        assert "Session State API" not in texts(at.warning), page_id


# ---- moving between pages inside the real app -------------------------------

def test_opening_a_topic_from_home_ticks_it_off_at_once_and_keeps_the_footer():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "⬜ 1 · Bits & Superposition" in texts(at.sidebar.markdown)
    at.button(key="home_t1").click().run()
    assert at.title[0].value == "Bits vs. Superposition"
    assert "✅ 1 · Bits & Superposition" in texts(at.sidebar.markdown)
    assert "Spelman College" in at.caption[-1].value


def test_footer_says_so_when_the_local_log_is_switched_on(ollama):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "nothing you type is stored" in at.caption[-1].value
    at.sidebar.checkbox[0].check().run()
    assert "nothing you type is stored" not in at.caption[-1].value
    assert "saved to a log file on this computer" in at.caption[-1].value


def test_footer_warns_when_a_cloud_model_is_picked_locally(ollama):
    ollama.models = ["local-model",
                     {"name": "big-model:cloud", "remote_host": "https://ollama.com"}]
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.selectbox[0].set_value("big-model:cloud").run()
    assert "sent to Ollama's cloud service" in at.caption[-1].value


def test_tyu_gives_no_feedback_until_the_class_password_is_given(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")      # hosted mode
    monkeypatch.setenv("APP_PASSWORD", "open-sesame")
    tutor.load_settings()
    at = submit(tyu(), "q1", MY_ANSWER)
    assert at.session_state["tyu_attempts"]["q1"][0]["feedback"] is None
    assert ollama.requests == []


def test_quick_check_feedback_stays_while_the_student_tries_the_page():
    at = run_page("t1")
    at.radio(key="quick_qc-t1-1").set_value("50% heads").run()
    at.button(key="quick_check_qc-t1-1").click().run()
    assert "Not quite" in texts(at.warning)
    at.toggle(key="t1_switch_on").set_value(False).run()     # go and try it
    assert "Not quite" in texts(at.warning)
    at.radio(key="quick_qc-t1-1").set_value("undefined until someone looks").run()
    assert "Not quite" not in texts(at.warning)     # a new choice needs a new check


def test_t1_clear_tally_lets_the_student_make_a_new_coin_prediction():
    at = run_page("t1")
    at.number_input(key="t1_coin100_prediction").set_value(50).run()
    at.button(key="t1_coin100_run").click().run()
    assert at.number_input(key="t1_coin100_prediction").disabled
    at.button(key="t1_clear").click().run()
    assert at.session_state["t1_tally"] == [0, 0]
    assert not at.number_input(key="t1_coin100_prediction").disabled
    assert at.number_input(key="t1_coin100_prediction").value is None


def test_t1_coin_prediction_can_be_made_again_without_clearing_the_tally():
    at = run_page("t1")
    at.number_input(key="t1_coin100_prediction").set_value(50).run()
    at.button(key="t1_coin100_run").click().run()
    assert at.number_input(key="t1_coin100_prediction").disabled
    at.button(key="t1_coin100_again").click().run()
    assert not at.number_input(key="t1_coin100_prediction").disabled
    assert at.number_input(key="t1_coin100_prediction").value is None
    assert sum(at.session_state["t1_tally"]) == 100     # the tally is kept
    at.number_input(key="t1_coin100_prediction").set_value(40).run()
    at.button(key="t1_coin100_run").click().run()
    assert sum(at.session_state["t1_tally"]) == 200


def test_t1_switch_prediction_can_be_made_again_without_flipping_the_switch():
    at = run_page("t1")
    at.number_input(key="t1_switch10_prediction").set_value(10).run()
    at.button(key="t1_switch10_run").click().run()
    assert at.number_input(key="t1_switch10_prediction").disabled
    at.button(key="t1_switch10_again").click().run()
    assert not at.number_input(key="t1_switch10_prediction").disabled
