"""
components/layout.py — the parts every page shares
==================================================

The list of pages, each page's title and introduction (read from
content/pages.yaml), the previous/next buttons, the sidebar progress list,
and the attribution footer.
"""

from pathlib import Path

import streamlit as st
import yaml

import tutor
from components import journey

ROOT = Path(__file__).parent.parent
PAGES_FILE = ROOT / "content" / "pages.yaml"

# Every page, in menu order: (page id, file, name in the menu).
# The folder is called "views", not "pages", on purpose: Streamlit serves
# a folder named "pages" by itself, bypassing app.py, so a reloaded page
# would lose its sidebar, tutor, and footer.
PAGES = [
    ("home", "views/home.py", "Home"),
    ("t1", "views/t1_bits.py", "1 · Bits & Superposition"),
    ("t2", "views/t2_oscillators.py", "2 · Coupled Oscillators"),
    ("t3", "views/t3_qubits.py", "3 · Electrons & Qubits"),
    ("t3b", "views/t3b_superposition_vs_mixture.py",
     "Go deeper: Superposition vs. mixture"),
    ("t4", "views/t4_phibits.py", "4 · Phi-Bit Systems"),
    ("tyu", "views/test_understanding.py", "Test Your Understanding"),
    ("journey", "views/my_journey.py", "My Journey"),
]
PAGE_FILES = {page_id: file for page_id, file, _ in PAGES}
PAGE_NAMES = {page_id: name for page_id, _, name in PAGES}

# The order the previous/next buttons walk through.
SEQUENCE = ["home", "t1", "t2", "t3", "t3b", "t4", "tyu", "journey"]

# The credit shown at the bottom of every page. Reword it here only.
ATTRIBUTION = (
    "Based on the *Superposition State Primer* created at **Spelman "
    "College**. This version was developed with the **Institute for Future "
    "Intelligence**."
)
STORAGE_NOTE_LOCAL = "Demonstration version: nothing you type is stored by this app."
STORAGE_NOTE_LOGGING = (
    "Tutor questions and answers are being saved to a log file on this "
    "computer, because the box in the sidebar is ticked."
)
STORAGE_NOTE_HOSTED = (
    "Demonstration version: questions and answers are sent to Ollama's cloud "
    "service to be answered and are not stored by this app."
)


@st.cache_data
def _load_pages(modified: float) -> dict:
    """Read pages.yaml. `modified` makes an edited file reload by itself."""
    return yaml.safe_load(PAGES_FILE.read_text(encoding="utf-8"))


def page_text(page_id: str) -> dict:
    """All the text for one page, from content/pages.yaml."""
    return _load_pages(PAGES_FILE.stat().st_mtime)[page_id]


def page_header(page_id: str) -> dict:
    """
    Draw the page's title and introduction and note the visit in the
    journey. Returns the page's text so the page can use its other entries.
    """
    text = page_text(page_id)
    st.title(text["title"])
    st.markdown(text["intro"])
    # Record a visit once per arrival, not on every slider move.
    if st.session_state.get("current_page") != page_id:
        st.session_state["current_page"] = page_id
        journey.record("page_visit", page_id)
    return text


def keep(key: str, default):
    """
    Call just before drawing a widget that has this key (and draw the
    widget WITHOUT its own default value).

    Streamlit forgets a widget's value when the student opens another
    page. Copying the value back into st.session_state on every run turns
    it into ordinary session data, which is kept, so sliders, choices, and
    predictions are still there when the student comes back.
    """
    st.session_state[key] = st.session_state.get(key, default)


def things_to_try(text: dict) -> None:
    """The page's numbered list of experiments to try."""
    items = text.get("things_to_try", [])
    if items:
        st.markdown("**Things to try**\n" + "\n".join(
            f"{i}. {item}" for i, item in enumerate(items, start=1)))


def go_to(page_id: str, preset: str | None = None) -> None:
    """
    Open another page. `preset` is handed to that page, which applies it
    when it loads (for example Topic 4 opened on the Superposition preset).
    """
    if preset:
        st.session_state[f"arrive_{page_id}"] = preset
    st.switch_page(PAGE_FILES[page_id])


def arrival_preset(page_id: str) -> str | None:
    """The preset another page asked this page to open with, if any."""
    return st.session_state.pop(f"arrive_{page_id}", None)


def prev_next(page_id: str) -> None:
    """Buttons to the previous and next page in the sequence."""
    at = SEQUENCE.index(page_id)
    st.divider()
    left, _, right = st.columns([1, 2, 1])
    if at > 0:
        before = SEQUENCE[at - 1]
        if left.button(f"← {PAGE_NAMES[before]}", key=f"prev_{page_id}"):
            go_to(before)
    if at < len(SEQUENCE) - 1:
        after = SEQUENCE[at + 1]
        if right.button(f"Next: {PAGE_NAMES[after]} →", key=f"next_{page_id}",
                        type="primary"):
            go_to(after)


def progress_sidebar(slot, question_count: int = 3) -> None:
    """
    List which topics were visited and how many questions were answered.
    `slot` is a sidebar placeholder made before the page ran; filling it
    afterwards means the list already includes what the student just did.
    """
    visited = {e["page"] for e in journey.events() if e["type"] == "page_visit"}
    answered = {e["details"].get("question_id") for e in journey.events()
                if e["type"] == "tyu_submit"}
    with slot:
        st.subheader("Progress")
        lines = [f"{'✅' if page_id in visited else '⬜'} {PAGE_NAMES[page_id]}"
                 for page_id in ("t1", "t2", "t3", "t3b", "t4")]
        lines.append(f"{'✅' if len(answered) >= question_count else '⬜'} "
                     f"Questions answered: {len(answered)} of {question_count}")
        st.markdown("  \n".join(lines))


def footer() -> None:
    """The attribution line at the bottom of every page."""
    if tutor.leaves_this_computer(st.session_state.get("tutor_model")):
        note = STORAGE_NOTE_HOSTED
    elif st.session_state.get("save_log"):
        note = STORAGE_NOTE_LOGGING
    else:
        note = STORAGE_NOTE_LOCAL
    st.divider()
    st.caption(f"{ATTRIBUTION} {note}")
