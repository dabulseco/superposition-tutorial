"""
tutor.py — the "Ask the tutor" feature, powered by an Ollama language model
===========================================================================

This file works in two modes, chosen automatically:

  LOCAL  (no API key set)  Talks to Ollama running on the same computer
                           (http://localhost:11434 by default). No student
                           question or answer is sent to an outside company.

  HOSTED (OLLAMA_API_KEY set)  Talks to Ollama's cloud service at
                           https://ollama.com, so the app can run on a web
                           host that has no Ollama of its own. Questions and
                           answers ARE sent to Ollama's servers in this mode.

WHAT THIS FILE DOES
-------------------
1. list_models()          -> asks Ollama which models are installed.
                             The order matches `ollama list` (newest first),
                             so the first model is the app's default.
2. build_system_prompt()  -> writes the tutor's instructions for one page:
                             its rules, the page's CURRENT settings (so
                             answers refer to what the student is looking
                             at), and reference notes from content/notes/.
3. stream_answer()        -> sends the conversation to the model and yields
                             the reply piece by piece (so text appears as it
                             is written). The tutor also proposes a few
                             questions to consider next; those are collected
                             separately so the app can show them as buttons.
   ask_text() / ask_json() -> one question, one complete answer. Used for
                             feedback on written answers (feedback.py).
4. log_interaction()      -> optionally saves each question and answer to a
                             local file (do not use with students without an
                             approved research protocol).
5. conversation_markdown() / conversation_html()
                          -> turn the conversation into a file the student
                             can download.

SETUP (one time)
----------------
    1. Install Ollama from https://ollama.com
    2. Download at least one chat model, for example:
           ollama pull llama3.2
    3. Make sure Ollama is running (the desktop app, or `ollama serve`).

To use an Ollama server on another machine, set the environment variable
OLLAMA_URL, e.g.  OLLAMA_URL=http://192.168.1.20:11434

SETTINGS FOR HOSTING ONLINE
---------------------------
Each can be an environment variable or a line in .streamlit/secrets.toml
(on Streamlit Community Cloud: the app's "Secrets" box).

    OLLAMA_API_KEY   your key from https://ollama.com/settings/keys
    APP_PASSWORD     students must type this before they can use the tutor
    OLLAMA_MODELS    optional, comma-separated models to offer,
                     e.g. "gemma4:31b, gpt-oss:120b"

Never put the key in this file or commit secrets.toml to GitHub.
"""

import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


def setting(name: str, default: str = "") -> str:
    """Read a setting from the environment, or else from Streamlit secrets."""
    value = os.environ.get(name)
    if value:
        return value.strip()
    try:
        import streamlit as st
        return str(st.secrets[name]).strip()
    except Exception:   # no secrets file, or this setting isn't in it
        return default


def load_settings() -> None:
    """
    Read the settings below. app.py calls this each time the page runs, so
    a change to secrets.toml takes effect without restarting the app.
    """
    global OLLAMA_API_KEY, HOSTED, OLLAMA_URL, APP_PASSWORD, HOSTED_MODELS

    # With a key we are in HOSTED mode and talk to Ollama's cloud service.
    OLLAMA_API_KEY = setting("OLLAMA_API_KEY")
    HOSTED = bool(OLLAMA_API_KEY)

    # Where Ollama is listening. Can be changed with the OLLAMA_URL setting.
    OLLAMA_URL = setting(
        "OLLAMA_URL", "https://ollama.com" if HOSTED else "http://localhost:11434"
    ).rstrip("/")

    # If set, students must enter this before the tutor will answer.
    APP_PASSWORD = setting("APP_PASSWORD")

    # Models offered in HOSTED mode (the first one available is the default).
    # The cloud catalogue is long, so we show only a few that suit tutoring.
    HOSTED_MODELS = [m.strip() for m in setting(
        "OLLAMA_MODELS", "gemma4:31b, gpt-oss:120b, gpt-oss:20b").split(",")
        if m.strip()]


load_settings()

# How many earlier messages to send with each new question. Keeping this
# small keeps answers fast on modest hardware.
MAX_HISTORY_MESSAGES = 10


# Names of models that run on Ollama's servers even in LOCAL mode.
REMOTE_MODELS: set[str] = set()


def leaves_this_computer(model: str | None) -> bool:
    """
    True if text sent to this model goes to Ollama's cloud: always in HOSTED
    mode, and in LOCAL mode for models Ollama marks as remote (their names
    usually end in "cloud").
    """
    if HOSTED:
        return True
    return bool(model) and (model in REMOTE_MODELS
                            or model.endswith(("-cloud", ":cloud")))


class OllamaUnavailable(Exception):
    """Raised when Ollama can't be reached or returns an error."""


DROPPED_MESSAGE = ("The connection to Ollama dropped before the answer was "
                   "finished. Please ask again.")


def _headers() -> dict:
    """The API key, sent with every request in HOSTED mode."""
    return {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if HOSTED else {}


# -----------------------------------------------------------------------------
# 1. Which models are installed?
# -----------------------------------------------------------------------------

def list_models() -> list[str]:
    """
    Return the names of installed models, in the same order as `ollama list`.

    Ollama's /api/tags endpoint is what the `ollama list` command itself uses,
    and it returns models sorted newest first. We keep that order, so the
    first name in the list is the default choice in the app.
    """
    try:
        reply = requests.get(f"{OLLAMA_URL}/api/tags", headers=_headers(),
                             timeout=10 if HOSTED else 3)
        reply.raise_for_status()
    except requests.RequestException as err:
        if HOSTED:
            raise OllamaUnavailable(
                f"Could not reach the Ollama cloud service at {OLLAMA_URL}. "
                "Try again in a moment."
            ) from err
        raise OllamaUnavailable(
            f"Could not reach Ollama at {OLLAMA_URL}. "
            "Start the Ollama app (or run `ollama serve`) and reload this page."
        ) from err

    listed = reply.json().get("models", [])
    available = [m["name"] for m in listed]
    # Ollama on a laptop can also list "cloud" models, which it forwards to
    # Ollama's servers. Remember them so the app can say where text goes.
    REMOTE_MODELS.update(m["name"] for m in listed if m.get("remote_host"))
    if HOSTED:
        # Offer only our short list, in our order. If none of those exist
        # any more, fall back to everything the service offers.
        chosen = [m for m in HOSTED_MODELS if m in available]
        return chosen or available
    return available


# -----------------------------------------------------------------------------
# 2. The tutor's instructions
# -----------------------------------------------------------------------------

# The tutor ends each reply with this line, then a short list of questions
# the student might consider next. The app shows them as buttons.
SUGGESTION_MARKER = "NEXT QUESTIONS:"
MAX_SUGGESTIONS = 3

# Reference notes the tutor must stay consistent with: one Markdown file per
# page (named after the page's id) plus shared.md, which is sent on every
# page. To give the tutor more background later (for example a study guide's
# instructions), add or edit files in this folder. No code change is needed.
NOTES_DIR = Path(__file__).parent / "content" / "notes"


def load_notes(page_id: str, notes_dir: Path | None = None) -> str:
    """
    Return the shared notes followed by this page's notes.
    A page without a notes file simply gets the shared notes.
    """
    folder = NOTES_DIR if notes_dir is None else Path(notes_dir)
    parts = []
    for name in ("shared", page_id):
        path = folder / f"{name}.md"
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)


def pending_prediction_rule(what: str) -> str:
    """
    A page rule for while the student still owes a prediction. `what`
    describes the question, e.g. "which patterns light up when ...".
    """
    return (
        f"PREDICTION PENDING. The page asks the student to predict {what}, "
        "and they have not done it yet. If they ask about it, do NOT state, "
        "confirm, or describe the outcome, not even in general terms, and "
        "do not quote a formula from the notes that settles it. Give one "
        "hint about what to think about, ask what they predict and why, "
        "and tell them to choose a prediction on the page to see for "
        "themselves.")


def normalize_math(text: str) -> str:
    """
    Some models write math as \\( ... \\) or \\[ ... \\] even when asked for
    $...$. Streamlit only draws the dollar form, so convert.
    """
    for bracket, dollars in ((r"\(", "$"), (r"\)", "$"), (r"\[", "$$"), (r"\]", "$$")):
        text = text.replace(bracket, dollars)
    return text


def _page_notes(page_id: str, notes_dir: Path | None = None) -> str:
    """One page's own notes, without the shared ones ("" if none)."""
    path = (NOTES_DIR if notes_dir is None else Path(notes_dir)) / f"{page_id}.md"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def build_system_prompt(context: dict, notes_dir: Path | None = None) -> str:
    """
    Write the tutor's instructions for one page, including its live settings.

    `context` is a dictionary each page builds to describe itself:
        page_id         short name of the page; also its notes file name
        page_title      the title the student sees
        controls        what the student can see or change on the page
        settings_lines  list of lines describing the current settings
        results_lines   list of lines with results (sent only if revealed)
        revealed        True once the student has run or measured
        hold_back       what must not be given away before that
        extra_rules     optional list of further rules for this page
        notes_pages     optional list of page ids whose notes to use
                        instead of this page's own
    """
    settings = "\n".join(f"- {line}" for line in context["settings_lines"])
    results = context.get("results_lines", [])

    if context["revealed"]:
        numbers = "\n".join(f"- {line}" for line in results)
        reveal_rule = ("The student has already run the experiment, so you "
                       "may discuss these numbers." if results else "")
    else:
        numbers = "- (The student has not run the experiment yet.)"
        reveal_rule = (
            "The student has NOT run the experiment yet. Do not state "
            f"{context.get('hold_back', 'the result')}. Help them reason "
            "toward a prediction instead."
        )

    # Rules special to this page go last and are labeled as overriding, so
    # a model doesn't let the general "explain it" rules win.
    extra_rules = ""
    if context.get("extra_rules"):
        extra_rules = (
            "\n\nRULES FOR THIS PAGE (these take priority over everything above)\n"
            + "\n".join(f"- {rule}" for rule in context["extra_rules"]))

    # Usually a page uses its own notes. A page can ask for other pages'
    # notes instead (Test Your Understanding draws on the topic pages).
    note_pages = list(dict.fromkeys(
        context.get("notes_pages", [context["page_id"]])))
    notes = "\n\n".join(filter(None, (
        [load_notes("shared", notes_dir)]
        + [_page_notes(page, notes_dir) for page in note_pages])))

    return f"""You are a patient physics tutor helping an undergraduate use an
interactive primer on superposition. Its topics are: classical bits and a
spinning coin; coupled oscillators; electrons and qubits; superposition
compared with a classical mixture; and phi-bits (sound-like waves on a chain
of weights and springs). The student is on the page "{context['page_title']}".

HOW TO ANSWER
- Use plain language for a STEM major who is new to quantum ideas.
- Keep answers short: usually 3 to 6 sentences. Offer to go deeper.
- Tie your answer to what the student can see or try on this page
  ({context['controls']}).
- If a question is outside this topic, say so in one sentence and steer back.
- If you are not sure, say so rather than guessing.
- Write math with $...$ (for example $P(+) = (1 + \\vec r \\cdot \\hat n)/2$).
- Stay consistent with the REFERENCE NOTES. Never invent numbers; use only
  the numbers given below or ones you compute from the formulas in the notes.

GUIDE, DON'T TELL
Your goal is for the student to reach the answer themselves.
- When the student asks something they could work out (a "why", a "what
  happens if", a prediction, a calculation), do NOT state the conclusion.
  Give one small hint or point to something to look at or try in the
  simulation, then ask ONE directed question that moves them a step closer.
- Build on what the student just said. Name what is right in their thinking
  before addressing what is not, and encourage them: effort and partial
  ideas deserve credit. Be warm but specific; avoid empty praise.
- When the student reasons their way to a correct answer, say so clearly
  and confirm it in a sentence, so they are not left unsure.
- If the student is wrong, don't just correct them. Ask a question or
  suggest an experiment in the simulation that exposes the problem.
- Answer directly, without a guiding question, when the student asks for a
  definition, what a symbol or control means, or how to use the page.
- Give the full explanation when the student has made two real attempts
  and is still stuck, or says plainly that they want to be told. Then ask
  them to check it against the simulation.

QUESTIONS TO CONSIDER NEXT
End EVERY reply with this block, exactly in this form, as the last thing
you write:

{SUGGESTION_MARKER}
- first question
- second question
- third question

Give two or three short questions (under 20 words each), worded as the
student would ask them, that take the next step from this conversation:
something to predict, test in the simulation, or explain. They must not
give away an answer, and they must respect the rule below about results
the student has not seen yet. Do not mention this block in your reply.

{reveal_rule}

CURRENT SETTINGS ON THE PAGE
{settings}
{numbers}

REFERENCE NOTES
{notes}{extra_rules}"""


# -----------------------------------------------------------------------------
# 3. Ask the model
# -----------------------------------------------------------------------------

def _post_chat(payload: dict) -> requests.Response:
    """
    Send one request to Ollama's /api/chat and return the reply, after
    turning every kind of failure into an OllamaUnavailable with a message
    a student or instructor can act on.
    """
    model = payload["model"]
    try:
        reply = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              headers=_headers(), stream=payload["stream"],
                              timeout=(5, 300))
    except requests.RequestException as err:
        raise OllamaUnavailable(f"Could not reach Ollama at {OLLAMA_URL}.") from err

    if reply.status_code in (401, 403):
        raise OllamaUnavailable(
            "Ollama rejected the API key. Check OLLAMA_API_KEY in the app's secrets.")
    if reply.status_code == 429:
        raise OllamaUnavailable(
            "The tutor has reached its usage limit for now. Try again later.")
    if reply.status_code != 200:
        # Ollama explains the problem in the body, e.g. a model that
        # can't chat (embedding models) or isn't fully downloaded.
        try:
            detail = reply.json().get("error", reply.text)
        except ValueError:
            detail = reply.text
        raise OllamaUnavailable(
            f"The model '{model}' could not answer: {detail}. "
            "If it is an embedding model (e.g. nomic-embed-text), pick a chat model instead."
        )
    return reply


def ask_text(model: str, system_prompt: str, user_text: str,
             temperature: float = 0.3, response_format=None) -> str:
    """
    Ask one question and wait for the whole answer (no streaming). Used for
    feedback on written answers, where the text is checked before the
    student sees it. Private <think> notes are removed.
    """
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_text}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    if response_format is not None:
        payload["format"] = response_format
    reply = _post_chat(payload)
    try:
        body = reply.json()
    except ValueError as err:
        raise OllamaUnavailable(DROPPED_MESSAGE) from err
    if "error" in body:
        raise OllamaUnavailable(body["error"])
    text = body.get("message", {}).get("content", "")
    return "".join(hide_thinking([text])).strip()


def ask_json(model: str, system_prompt: str, user_text: str, schema: dict) -> dict | list:
    """
    Ask for an answer in a fixed JSON shape. `schema` is a JSON schema that
    Ollama uses to constrain what the model may write. Temperature 0 makes
    the same answer get the same check each time.

    Raises ValueError if the reply still isn't valid JSON, so the caller
    can retry or fall back.
    """
    return json.loads(ask_text(model, system_prompt, user_text,
                               temperature=0.0, response_format=schema))



def stream_answer(model: str, system_prompt: str, history: list[dict],
                  suggestions: list | None = None):
    """
    Send the conversation to Ollama and yield the answer as it is written.

    history     : list of {"role": "user"|"assistant", "content": "..."}
                  The newest student question must be the last item.
    suggestions : an empty list. When the answer is finished it holds the
                  tutor's "questions to consider next", which are kept out
                  of the answer text.
    """
    # Send only the role and text; messages also carry notes for the
    # downloadable transcript (time, settings) that the model doesn't need.
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m["role"], "content": m["content"]}
                 for m in history[-MAX_HISTORY_MESSAGES:]]

    reply = _post_chat({
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.3},   # low = steadier, less inventive
    })

    # Ollama sends one JSON object per line while it writes.
    def pieces():
        finished = False
        try:
            for line in reply.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if "error" in chunk:
                    raise OllamaUnavailable(chunk["error"])
                yield chunk.get("message", {}).get("content", "")
                if chunk.get("done"):
                    finished = True
                    break
        except (requests.RequestException, ValueError) as err:
            raise OllamaUnavailable(DROPPED_MESSAGE) from err
        # Ollama always ends with a "done" line. Without it the connection
        # was cut, and showing half an answer as if complete would mislead.
        if not finished:
            raise OllamaUnavailable(DROPPED_MESSAGE)

    # "Reasoning" models (e.g. deepseek-r1, qwen3) may write private notes
    # inside <think>...</think>. Students should see only the answer.
    if suggestions is None:
        suggestions = []
    yield from split_suggestions(hide_thinking(pieces()), suggestions)


def split_suggestions(pieces, suggestions: list):
    """
    Pass the answer through, but stop at the NEXT QUESTIONS block. The
    questions in that block are put into `suggestions` instead of shown.

    The marker can be split across pieces, and a model may decorate it
    (e.g. "**NEXT QUESTIONS:**"), so a little text is held back until we
    know it is not the start of the block.
    """
    marker = SUGGESTION_MARKER.rstrip(":").lower()
    hold = len(marker) + 8          # room for the marker plus decoration
    buffer = ""
    tail = None                     # text after the marker, once it is seen

    for piece in pieces:
        if tail is not None:
            tail += piece
            continue
        buffer += piece
        at = buffer.lower().find(marker)
        if at != -1:
            tail = buffer[at + len(marker):]
            before = buffer[:at].rstrip(" \t\n*#_-")
            if before:
                yield before
        elif len(buffer) > hold:
            yield buffer[:-hold]
            buffer = buffer[-hold:]

    if tail is None:
        if buffer:
            yield buffer
        return

    for line in tail.splitlines():
        question = line.strip(" \t*#_:-•").lstrip("0123456789.) ").strip()
        if question and len(suggestions) < MAX_SUGGESTIONS:
            suggestions.append(question)


def hide_thinking(pieces):
    """
    Pass text through, dropping anything between <think> and </think>.

    The tags can be split across pieces, so a few characters are held back
    until we know they are not the start of a tag.
    """
    OPEN, CLOSE = "<think>", "</think>"
    inside = False
    buffer = ""

    for piece in pieces:
        buffer += piece
        out = ""
        while buffer:
            if inside:
                end = buffer.find(CLOSE)
                if end == -1:
                    buffer = buffer[-len(CLOSE):]      # keep a possible partial tag
                    break
                buffer = buffer[end + len(CLOSE):]
                inside = False
            else:
                start = buffer.find(OPEN)
                if start == -1:
                    safe = len(buffer) - (len(OPEN) - 1)
                    if safe > 0:
                        out += buffer[:safe]
                        buffer = buffer[safe:]
                    break
                out += buffer[:start]
                buffer = buffer[start + len(OPEN):]
                inside = True
        if out:
            yield out

    if buffer and not inside:
        yield buffer


# -----------------------------------------------------------------------------
# 4. Optional local log
# -----------------------------------------------------------------------------

def log_interaction(path: Path, model: str, context: dict,
                    question: str, answer: str) -> None:
    """
    Append one question/answer pair to a JSON Lines file (one record per line).
    Nothing leaves this computer. Contains no names unless a student types one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model,
        "page": context["page_id"],
        "settings": settings_text(context),
        "question": question,
        "answer": answer,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# -----------------------------------------------------------------------------
# 5. Downloadable transcript
# -----------------------------------------------------------------------------

def settings_text(context: dict) -> str:
    """One line describing the page when a question was asked."""
    text = "; ".join(context["settings_lines"])
    if not context["revealed"]:
        return f"{text}; experiment not yet run" if text else "experiment not yet run"
    results = "; ".join(context.get("results_lines", []))
    return "; ".join(part for part in (text, results) if part)


def _speaker(msg: dict) -> str:
    return "Student" if msg["role"] == "user" else "Tutor"


def _source(msg: dict) -> str:
    """Did the student type this question, or click a suggested one?"""
    return ("clicking a suggested question" if msg.get("suggested")
            else "typing")


def conversation_markdown(chat: list[dict], title: str = "Tutor conversation") -> str:
    """The whole conversation as a Markdown document."""
    exported = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [f"# {title}", "", f"Exported (UTC): {exported}", ""]
    for msg in chat:
        lines += [f"## {_speaker(msg)}", ""]
        if msg["role"] == "user":
            lines += [f"*Time (UTC): {msg.get('time', 'unknown')}*  ",
                      f"*Page settings: {msg.get('settings', 'unknown')}*  ",
                      f"*Asked by: {_source(msg)}*", ""]
        else:
            lines += [f"*Model: {msg.get('model', 'unknown')}*", ""]
        lines += [msg["content"], ""]
        if msg.get("suggestions"):
            lines += ["*Questions the tutor suggested next:*", ""]
            lines += [f"- {q}" for q in msg["suggestions"]] + [""]
    return "\n".join(lines)


# Shared by every downloadable web page (conversation and My Journey).
PAGE_STYLE = """
  body { font-family: system-ui, sans-serif; max-width: 46rem;
         margin: 2rem auto; padding: 0 1rem; line-height: 1.5; color: #222; }
  section { border-left: 4px solid #999; padding: 0.2rem 1rem; margin: 1rem 0; }
  section.user { border-color: #c98a00; }
  section.assistant { border-color: #1f5fbf; }
  h2 { font-size: 1rem; margin: 0.4rem 0 0; }
  .note { color: #666; font-size: 0.85rem; margin: 0.2rem 0 0.6rem; }
  .text { white-space: pre-wrap; }
"""


def html_page(title: str, body: str) -> str:
    """
    Wrap already-escaped HTML in one self-contained web page. Math written
    with $...$ is drawn by MathJax when the reader is online, and stays
    readable as plain text when they are not.
    """
    exported = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{PAGE_STYLE}</style>
<script>
  MathJax = {{ tex: {{ inlineMath: [["$", "$"]] }} }};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p class="note">Exported (UTC): {exported}</p>
{body}
</body>
</html>
"""


def conversation_html(chat: list[dict], title: str = "Tutor conversation") -> str:
    """
    The whole conversation as one self-contained web page.

    All text is escaped, so nothing a student or the model typed can run as
    code.
    """
    parts = []
    for msg in chat:
        if msg["role"] == "user":
            note = (f"Time (UTC): {html.escape(str(msg.get('time', 'unknown')))}"
                    f"<br>Page settings: {html.escape(str(msg.get('settings', 'unknown')))}"
                    f"<br>Asked by: {_source(msg)}")
        else:
            note = f"Model: {html.escape(str(msg.get('model', 'unknown')))}"
        suggested = ""
        if msg.get("suggestions"):
            items = "".join(f"<li>{html.escape(q)}</li>" for q in msg["suggestions"])
            suggested = (f'<p class="note">Questions the tutor suggested next:</p>\n'
                         f"<ul>{items}</ul>\n")
        parts.append(
            f'<section class="{msg["role"]}">\n'
            f"<h2>{_speaker(msg)}</h2>\n"
            f'<p class="note">{note}</p>\n'
            f'<div class="text">{html.escape(msg["content"])}</div>\n'
            f"{suggested}"
            f"</section>")
    return html_page(title, "\n".join(parts))
