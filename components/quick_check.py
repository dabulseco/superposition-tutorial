"""
components/quick_check.py — two short questions at the end of each topic
========================================================================

Multiple-choice items from content/quick_checks.yaml. A wrong choice gets a
hint that points back to the simulation, not the answer, so the student
can try again. Each check is noted in the journey.

To hide quick checks, empty content/quick_checks.yaml (see that file).
"""

import streamlit as st

import feedback
from components import journey, layout


def quick_check(page_id: str) -> None:
    """Draw this page's quick-check items, if there are any."""
    try:
        items = [item for item in feedback.load_quick_checks(
            valid_pages=set(layout.PAGE_FILES)) if item["page"] == page_id]
    except feedback.ContentError as err:
        st.error(str(err))
        return
    if not items:
        return

    st.divider()
    st.subheader("Quick check")
    for item in items:
        item_id = item["id"]
        with st.container(border=True):
            layout.keep(f"quick_{item_id}", None)
            choice = st.radio(item["question"],
                              [o["text"] for o in item["options"]],
                              key=f"quick_{item_id}")
            checked_key = f"quick_checked_{item_id}"
            if st.button("Check", key=f"quick_check_{item_id}"):
                if choice is None:
                    st.info("Choose an answer first.")
                    continue
                option = next(o for o in item["options"] if o["text"] == choice)
                journey.record("quick_check", page_id, item_id=item_id,
                               question=item["question"], choice=choice,
                               correct=bool(option.get("correct")))
                # Remembered, so the hint stays up while the student goes
                # back to the simulation to try what it suggests.
                st.session_state[checked_key] = choice

            if choice is not None and st.session_state.get(checked_key) == choice:
                option = next(o for o in item["options"] if o["text"] == choice)
                if option.get("correct"):
                    st.success("Correct.")
                else:
                    st.warning(f"Not quite. {option['feedback']} "
                               f"{item.get('try', '')}")
