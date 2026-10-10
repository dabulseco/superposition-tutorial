"""
Superposition State Primer — an interactive primer for undergraduates
=====================================================================

WHAT THIS APP IS
----------------
A four-topic introduction to superposition, based on the Superposition State
Primer created at Spelman College:

    1  Bits & Superposition      a light switch beside a spinning coin
    2  Coupled Oscillators       two weights on springs and their two patterns
    3  Electrons & Qubits        a qubit on the Bloch sphere, measured
       Go deeper                 superposition vs. a classical mixture
    4  Phi-Bit Systems           sound-like waves on a chain of weights
    Test Your Understanding      three open questions with feedback
    My Journey                   what the student did during this visit

Every topic follows predict -> observe -> explain, and every page ends with
an "Ask your own questions" chat answered by a language model through
Ollama (on this computer by default).

HOW TO RUN
----------
    conda activate superposition
    pip install -r requirements.txt
    streamlit run app.py

CODE LAYOUT
-----------
    app.py         this file: the menu, the sidebar, and the footer
    views/         one file per page
    physics/       the physics, with no Streamlit and no language model in
                   it, so every number a student sees comes from tested code
    components/    pieces the pages share (chat, prediction gate, plots)
    content/       the words: page text, questions, and the tutor's notes
    tutor.py       talking to the language model
    feedback.py    feedback on Test Your Understanding answers
    tests/         automated checks (run with: pytest)

WHAT IS STORED
--------------
Nothing. A student's activity is kept only in their browser tab, and they
can download it from the My Journey page.
"""

import streamlit as st

import feedback
import tutor
from components import layout
from components.chat_panel import model_picker


def main():
    st.set_page_config(page_title="Superposition State Primer", layout="wide")
    tutor.load_settings()   # pick up any change to the key or password

    pages = [st.Page(file, title=name, default=(page_id == "home"))
             for page_id, file, name in layout.PAGES]
    current = st.navigation(pages)

    # The sidebar is drawn before the page so the page's chat knows which
    # model was picked.
    progress_slot = st.sidebar.container()
    model_picker()

    # A typo in the questions file should be visible at once, on any page.
    question_count = 3
    try:
        question_count = len(
            feedback.load_questions(valid_pages=set(layout.PAGE_FILES)))
        feedback.load_quick_checks(valid_pages=set(layout.PAGE_FILES))
    except feedback.ContentError as err:
        st.error(str(err))

    current.run()
    # Filled in after the page ran, so it counts what the student just did.
    layout.progress_sidebar(progress_slot, question_count)
    layout.footer()


main()
