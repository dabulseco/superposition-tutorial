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


# -----------------------------------------------------------------------------
# Reading the record back: summary, plain-language lines, and downloads
# -----------------------------------------------------------------------------

TOPIC_PAGES = ("t1", "t2", "t3", "t3b", "t4")


def _matched(details: dict):
    """
    Did an either/or prediction come true? None if this event has no such
    prediction. "About how many?" predictions are not scored: a guess of
    50 that meets 48 heads is a good prediction, not a miss.
    """
    if details.get("prediction") is None or "matched" not in details:
        return None
    return bool(details["matched"])


def summary(events: list[dict]) -> dict:
    """Headline counts for the top of the My Journey page."""
    predictions = [_matched(e["details"]) for e in events]
    predictions = [m for m in predictions if m is not None]
    return {
        "topics": len({e["page"] for e in events
                       if e["type"] == "page_visit" and e["page"] in TOPIC_PAGES}),
        "predictions": len(predictions),
        "matched": sum(predictions),
        "answers": sum(e["type"] == "tyu_submit" for e in events),
        "questions": sum(e["type"] == "chat_question" for e in events),
    }


def describe(event: dict, page_names: dict) -> str:
    """One plain-language line saying what happened."""
    d = event["details"]
    kind = event["type"]
    verdict = {True: "matched", False: "did not match", None: ""}[_matched(d)]
    off_by = d.get("off_by")

    if kind == "page_visit":
        return "Opened this page"
    if kind == "preset":
        return f"Chose the preset “{d.get('name')}”"
    if kind == "measure_bit":
        return f"Measured the switch: it read {d.get('result')}"
    if kind == "measure_bit_10":
        return (f"Predicted {d.get('prediction')} ON readings out of 10; "
                f"the switch read ON {d.get('times_on')} times ({verdict})")
    if kind == "measure_coin":
        return f"Slapped the coin down: {d.get('result')}"
    if kind == "measure_100_coins":
        return (f"Predicted {d.get('prediction')} heads out of 100; got "
                f"{d.get('heads')} (off by {d.get('off_by')})")
    if kind == "positions_set":
        return (f"Set weight 1 to {d.get('x1')} and weight 2 to {d.get('x2')}: "
                f"Pattern 1 amplitude {d.get('pattern_1'):g}, "
                f"Pattern 2 amplitude {d.get('pattern_2'):g}")
    if kind == "prediction":
        return (f"Predicted “{d.get('prediction')}”; the result was "
                f"“{d.get('outcome')}” ({verdict})")
    if kind == "measure_1":
        return f"Measured one qubit at {d.get('percent_up')}% UP: {d.get('result')}"
    if kind == "measure_same_again":
        return f"Measured the same qubit again: still {d.get('result')}"
    if kind == "measure_100":
        return (f"At {d.get('percent_up')}% UP, predicted {d.get('prediction')} "
                f"UP out of 100; got {d.get('ups')} (off by {d.get('off_by')})")
    if kind == "run":
        return (f"Ran the experiment (θ = {d.get('theta')}°, φ = {d.get('phi')}°, "
                f"{d.get('axis')}): predicted “{d.get('prediction')}”; the "
                f"result was “{d.get('outcome')}” ({verdict})")
    if kind == "mixer_set":
        return (f"Set LEFT {d.get('left')}%, RIGHT {d.get('right')}%, phase "
                f"{d.get('phase')}°: {d.get('status')}")
    if kind == "go_deeper_open":
        return "Opened “Go deeper: Superposition vs. mixture” from here"
    if kind == "revisit_link":
        return (f"Followed a revisit link to "
                f"{page_names.get(d.get('to'), d.get('to'))}")
    if kind == "quick_check":
        return (f"Quick check: chose “{d.get('choice')}” "
                f"({'correct' if d.get('correct') else 'not correct'})")
    if kind == "tyu_submit":
        return f"Submitted attempt {d.get('attempt')} for: {d.get('question')}"
    if kind == "chat_question":
        return f"Asked the tutor: {d.get('question')}"
    # A kind added later still shows up, just less prettily.
    return f"{kind}: " + ", ".join(f"{k} = {v}" for k, v in d.items())


def extra_text(event: dict) -> list[tuple[str, str]]:
    """Longer text that belongs under an event: (label, text) pairs."""
    d = event["details"]
    if event["type"] == "tyu_submit":
        parts = [("Answer", d.get("answer") or "")]
        if d.get("confidence"):
            parts.append(("Confidence", f"{d['confidence']} of 5"))
        parts.append(("Feedback", d.get("feedback") or "none available"))
        return parts
    if event["type"] == "chat_question":
        return [("Tutor's answer", d.get("answer") or "")]
    return []


def by_page(events: list[dict]) -> dict:
    """Events grouped by page, pages in the order they were first used."""
    groups = {}
    for event in events:
        groups.setdefault(event["page"], []).append(event)
    return groups


def to_markdown(events: list[dict], page_names: dict) -> str:
    """The whole journey as a Markdown document."""
    exported = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = ["# My Journey: Superposition State Primer", "",
             f"Exported (UTC): {exported}", ""]
    if not events:
        lines.append("Nothing recorded yet.")
    for page, page_events in by_page(events).items():
        lines += [f"## {page_names.get(page, page)}", ""]
        for event in page_events:
            lines.append(f"- *{event['time']}* — {describe(event, page_names)}")
            for label, text in extra_text(event):
                lines.append(f"  - {label}: {text}")
        lines.append("")
    return "\n".join(lines)


def to_html(events: list[dict], page_names: dict) -> str:
    """
    The whole journey as one self-contained web page. Everything the
    student or the model wrote is escaped, so none of it can run as code.
    """
    import html

    import tutor
    from components import layout   # imported here: layout imports this file

    parts = [] if events else ["<p>Nothing recorded yet.</p>"]
    for page, page_events in by_page(events).items():
        items = []
        for event in page_events:
            extras = "".join(
                f'<div class="text"><strong>{html.escape(label)}:</strong> '
                f"{html.escape(text)}</div>"
                for label, text in extra_text(event))
            items.append(
                f'<li><span class="note">{html.escape(event["time"])}</span> '
                f"{html.escape(describe(event, page_names))}{extras}</li>")
        parts.append(f"<section><h2>{html.escape(page_names.get(page, page))}"
                     f"</h2>\n<ul>{''.join(items)}</ul></section>")
    credit = html.escape(layout.ATTRIBUTION.replace("*", ""))
    parts.append(f'<p class="note">{credit}</p>')
    return tutor.html_page("My Journey: Superposition State Primer",
                           "\n".join(parts))
