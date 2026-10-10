"""
components/journey.py — a record of what the student did, for this visit only
=============================================================================

Each page calls record() when the student does something worth remembering
(makes a prediction, runs a measurement, submits an answer, asks a question).
The "My Journey" page shows the list and lets the student download it.

WHERE THE RECORD LIVES
----------------------
Only in this browser tab's session (st.session_state). Nothing is written
to disk or sent anywhere, and it is gone when the tab closes. This file is
the one place a saved record could be added later, once a research protocol
(IRB approval and consent) is in place.
"""

from datetime import datetime, timezone

import streamlit as st


def record(event_type: str, page: str, **details) -> None:
    """Add one event. `details` holds whatever numbers or text describe it."""
    st.session_state.setdefault("journey", []).append({
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "page": page,
        "type": event_type,
        "details": details,
    })


def events() -> list[dict]:
    """Every event recorded so far, oldest first."""
    return st.session_state.setdefault("journey", [])
