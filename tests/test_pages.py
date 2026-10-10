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
