"""
pages/my_journey.py — My Journey: what the student did during this visit
========================================================================

A timeline of the student's own activity: topics opened, predictions and
whether they matched, measurements, each submitted answer with its
feedback, and the questions they asked the tutor.

The record exists only in this browser tab (see components/journey.py).
Students who want to keep it download it as a web page or as Markdown.
"""

from datetime import datetime

import streamlit as st

from components import journey, layout

PAGE_ID = "journey"

text = layout.page_header(PAGE_ID)
st.warning("This record exists only in this browser tab. It is gone when "
           "you close the tab. Download it to keep it.")

# This page's own visit is not interesting to read about.
events = [e for e in journey.events() if e["page"] != PAGE_ID]
names = layout.PAGE_NAMES

if not events:
    st.info("Nothing here yet. Work through a topic, then come back.")
else:
    counts = journey.summary(events)
    cols = st.columns(4)
    cols[0].metric("Topics opened", f"{counts['topics']} of 5")
    cols[1].metric("Predictions that matched",
                   f"{counts['matched']} of {counts['predictions']}")
    cols[2].metric("Answers submitted", str(counts["answers"]))
    cols[3].metric("Questions asked", str(counts["questions"]))

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    col_html, col_md, _ = st.columns([1, 1, 2])
    col_html.download_button(
        "Download as HTML", journey.to_html(events, names),
        file_name=f"my-journey-{stamp}.html", mime="text/html",
        help="A web page that opens in any browser. Print it to make a PDF.")
    col_md.download_button(
        "Download as Markdown", journey.to_markdown(events, names),
        file_name=f"my-journey-{stamp}.md", mime="text/markdown",
        help="Plain text that is easy to analyze later.")

    st.subheader("Timeline, page by page")
    for page, page_events in journey.by_page(events).items():
        with st.expander(f"{names.get(page, page)} ({len(page_events)})",
                         expanded=True):
            for event in page_events:
                clock = event["time"][11:19]
                st.markdown(f"`{clock}` {journey.describe(event, names)}")
                for label, body in journey.extra_text(event):
                    st.markdown(f"> **{label}:** " + body.replace("\n", "\n> "))
    st.caption("Times are in UTC.")

layout.prev_next(PAGE_ID)
