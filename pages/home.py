"""
pages/home.py — the front page
==============================

Explains the one story that runs through the four topics, links to each of
them, and offers a general chat for questions about the whole primer.
"""

import streamlit as st

from components import layout
from components.chat_panel import chat_panel

PAGE_ID = "home"

# One line per topic: (page id, what it shows, the two basic states).
STORY = [
    ("t1", "A bit is in one state. A spinning coin is a first picture of "
           "being in two at once.", "ON / OFF, HEADS / TAILS"),
    ("t2", "Two weights on springs can play two patterns at the same time.",
     "Pattern 1 / Pattern 2"),
    ("t3", "A qubit combines UP and DOWN with chosen probabilities.",
     "UP / DOWN"),
    ("t3b", "The experiment that tells a superposition from "
            "\"one or the other, we just don't know which\".",
     "superposition / mixture"),
    ("t4", "Sound-like waves on a chain of weights can carry a qubit-like "
           "superposition.", "left wave / right wave"),
]

text = layout.page_header(PAGE_ID)

st.subheader("One story, four topics")
st.markdown(
    "Each topic has **two basic states** and a way to **combine** them. "
    "On every topic you will predict what happens, try it, and then explain "
    "it. Start with Topic 1 and work down.")

for page_id, what, states in STORY:
    left, middle, right = st.columns([1.3, 2.4, 1.3])
    if left.button(layout.PAGE_NAMES[page_id], key=f"home_{page_id}",
                   width="stretch"):
        layout.go_to(page_id)
    middle.markdown(what)
    right.caption(f"Basic states: {states}")

st.markdown(
    "When you have worked through the topics, go to **Test Your "
    "Understanding** to answer three questions in your own words, and to "
    "**My Journey** to see and download what you did.")

chat_panel({
    "page_id": PAGE_ID,
    "page_title": text["title"],
    "controls": "links to the four topics, Test Your Understanding, and My Journey",
    "settings_lines": ["The student is on the home page and has not opened "
                       "a simulation here."],
    "revealed": True,
}, starter_questions=text["starter_questions"])

layout.prev_next(PAGE_ID)
