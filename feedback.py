"""
feedback.py — feedback on "Test Your Understanding" answers
===========================================================

WHAT THIS FILE DOES
-------------------
1. load_questions()  reads the questions (and any rubric) from
                     content/questions.yaml and checks the file for mistakes.
2. give_feedback()   asks the language model for formative feedback on one
                     answer: a strength, a guiding question, and a pointer to
                     a simulation. It never gives a grade and never writes
                     the answer for the student.

TWO MODES, CHOSEN BY THE QUESTIONS FILE
---------------------------------------
  No rubric (key_ideas is empty)
      One call to the model: general guided feedback.

  With a rubric (key_ideas filled in)
      Step 1  The model checks the answer against each key idea and returns
              JSON, quoting the student's words as evidence.
      Checks  Code (not the model) verifies each quote really appears in
              the answer. An idea "found" with an invented quote is not
              credited. Unknown ids are thrown away.
      Step 2  The model writes the feedback from the checked result.
      Check   Code rejects feedback that states a key idea the student has
              not reached yet, since that would hand over the answer.

To add a rubric, edit content/questions.yaml. No code change is needed.

If the model can't produce usable output after one retry, the student sees
a short neutral message and the attempt is marked "flagged" so an
instructor can look at it.
"""

import re
from pathlib import Path

import yaml

import tutor

QUESTIONS_FILE = Path(__file__).parent / "content" / "questions.yaml"

LEVELS = ("beginning", "developing", "proficient")
STATUSES = ("present", "absent")

FALLBACK_TEXT = ("Thanks for your answer. Try revisiting the simulation "
                 "below, then come back and revise your answer.")

# Feedback is rejected if it repeats more than this fraction of the
# meaningful words of a key idea the student hasn't reached.
COPY_THRESHOLD = 0.6


class ContentError(Exception):
    """Raised when a content file has a mistake, with a message naming it."""


# -----------------------------------------------------------------------------
# 1. The questions file
# -----------------------------------------------------------------------------

def _require(condition: bool, path: Path, problem: str) -> None:
    if not condition:
        raise ContentError(f"Problem in {path.name}: {problem}")


# The only entries each part of the files may have. Anything else is
# almost always a typo (key_idea for key_ideas) or a line YAML split at a
# comma, and silently ignoring it would switch a rubric off without warning.
QUESTION_KEYS = {"id", "text", "revisit", "key_ideas", "misconceptions"}
ENTRY_KEYS = {"id", "text", "advanced"}
REVISIT_KEYS = {"label", "page", "preset"}
ITEM_KEYS = {"id", "page", "question", "try", "options"}
OPTION_KEYS = {"text", "correct", "feedback"}

# Presets a revisit link may ask a page to open on.
PRESETS = {"t4": {"superposition"}}


def _read_yaml(path: Path):
    """Read a YAML file, turning every way it can fail into a ContentError."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContentError(f"Problem in {path.name}: the file is missing "
                           f"(expected at {path})") from None
    except UnicodeDecodeError:
        raise ContentError(
            f"Problem in {path.name}: the file is not saved as UTF-8 text. "
            f"Re-save it with UTF-8 encoding (curly quotes pasted from a "
            f"word processor are the usual cause).") from None
    except yaml.YAMLError as err:
        raise ContentError(f"Problem in {path.name}: the file is not valid "
                           f"YAML ({err})") from err


def _only_keys(entry: dict, allowed: set, path: Path, where: str) -> None:
    extra = [str(key) for key in entry if key not in allowed]
    _require(not extra, path,
             f"{where} has an entry the app does not know: "
             f"{', '.join(repr(k) for k in extra)}. Allowed: "
             f"{', '.join(sorted(allowed))}. (If the text contains a comma "
             f"or colon, put it in quotation marks.)")


def _is_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_entries(entries, path: Path, where: str, seen: set) -> list[dict]:
    """Key ideas or misconceptions: each needs a unique id and some text."""
    _require(isinstance(entries, list), path, f"{where} must be a list")
    for entry in entries:
        _require(isinstance(entry, dict) and _is_text(entry.get("id")), path,
                 f"an entry in {where} is missing its id")
        _only_keys(entry, ENTRY_KEYS, path, f"{entry['id']} in {where}")
        _require(isinstance(entry.get("text"), str) and entry["text"].strip(),
                 path, f"{entry['id']} in {where} is missing its text")
        _require(entry["id"] not in seen, path,
                 f"the id {entry['id']} is used more than once")
        seen.add(entry["id"])
    return entries


def load_questions(path: Path | None = None, valid_pages=None) -> list[dict]:
    """
    Read and check the questions file. Returns the list of questions.

    valid_pages : the page ids a "revisit" entry may point to. Leave as
                  None to skip that check.
    Raises ContentError, naming the file and the problem, if anything is
    wrong, so a typo shows up at startup rather than in front of a student.
    """
    path = QUESTIONS_FILE if path is None else Path(path)
    data = _read_yaml(path)

    _require(isinstance(data, dict) and isinstance(data.get("questions"), list)
             and data["questions"], path,
             "it must start with 'questions:' followed by a list")

    seen_ids = set()
    for question in data["questions"]:
        _require(isinstance(question, dict) and _is_text(question.get("id")),
                 path, "a question is missing its id (ids are plain text, "
                       "for example q1)")
        qid = question["id"]
        _only_keys(question, QUESTION_KEYS, path, f"question {qid}")
        _require(qid not in seen_ids, path,
                 f"the question id {qid} is used more than once")
        seen_ids.add(qid)
        _require(isinstance(question.get("text"), str)
                 and question["text"].strip(), path,
                 f"question {qid} is missing its text")

        revisit = question.get("revisit")
        _require(isinstance(revisit, list) and revisit, path,
                 f"question {qid} needs at least one revisit entry")
        for link in revisit:
            _require(isinstance(link, dict) and _is_text(link.get("label"))
                     and _is_text(link.get("page")), path,
                     f"a revisit entry of {qid} needs a label and a page, "
                     f"both as text")
            _only_keys(link, REVISIT_KEYS, path, f"a revisit entry of {qid}")
            preset = link.get("preset")
            _require(preset is None or preset in PRESETS.get(link["page"], ()),
                     path, f"question {qid} asks page '{link['page']}' for a "
                           f"preset '{preset}' that it does not have")
            _require(valid_pages is None or link["page"] in valid_pages, path,
                     f"question {qid} has a revisit page '{link['page']}' "
                     f"that is not a page of the app")

        question["key_ideas"] = _check_entries(
            question.get("key_ideas") or [], path, f"key_ideas of {qid}", seen_ids)
        question["misconceptions"] = _check_entries(
            question.get("misconceptions") or [], path,
            f"misconceptions of {qid}", seen_ids)
        for idea in question["key_ideas"]:
            idea["advanced"] = bool(idea.get("advanced", False))
    return data["questions"]


QUICK_CHECKS_FILE = Path(__file__).parent / "content" / "quick_checks.yaml"


def load_quick_checks(path: Path | None = None, valid_pages=None) -> list[dict]:
    """
    Read and check the quick-check items (short multiple-choice questions
    shown at the end of each topic). An empty or missing file returns an
    empty list, which hides the feature.

    Raises ContentError, naming the file and the problem, for a mistake.
    """
    path = QUICK_CHECKS_FILE if path is None else Path(path)
    if not path.is_file():
        return []
    data = _read_yaml(path) or {}
    _require(isinstance(data, dict), path,
             "it must start with 'items:' followed by a list")
    items = data.get("items") or []
    _require(isinstance(items, list), path, "'items' must be a list")

    seen = set()
    for item in items:
        _require(isinstance(item, dict) and _is_text(item.get("id")), path,
                 "an item is missing its id")
        item_id = item["id"]
        _only_keys(item, ITEM_KEYS, path, f"item {item_id}")
        _require(item_id not in seen, path,
                 f"the id {item_id} is used more than once")
        seen.add(item_id)
        _require(isinstance(item.get("question"), str)
                 and item["question"].strip(), path,
                 f"item {item_id} is missing its question")
        _require(valid_pages is None or item.get("page") in valid_pages, path,
                 f"item {item_id} has a page '{item.get('page')}' that is "
                 f"not a page of the app")
        options = item.get("options")
        _require(isinstance(options, list) and len(options) >= 2, path,
                 f"item {item_id} needs at least two options")
        for option in options:
            _require(isinstance(option, dict) and _is_text(option.get("text")),
                     path, f"an option of {item_id} is missing its text "
                           f"(put numbers in quotation marks)")
            _only_keys(option, OPTION_KEYS, path, f"an option of {item_id}")
        texts = [option["text"] for option in options]
        _require(len(set(texts)) == len(texts), path,
                 f"item {item_id} lists the same option more than once")
        _require(sum(bool(o.get("correct")) for o in options) == 1, path,
                 f"item {item_id} must have exactly one option marked "
                 f"'correct: true'")
        for option in options:
            _require(option.get("correct") or option.get("feedback"), path,
                     f"the option '{option['text']}' of {item_id} needs "
                     f"feedback (every wrong option does)")
    return items


def has_rubric(question: dict) -> bool:
    """True once key ideas have been written for this question."""
    return bool(question["key_ideas"])


# -----------------------------------------------------------------------------
# 2. Feedback
# -----------------------------------------------------------------------------

WRITING_RULES = """RULES FOR THE FEEDBACK
- Write 3 to 5 sentences, in plain and encouraging language, to the student.
- Name ONE specific strength, quoting a few of the student's own words in
  quotation marks.
- Point to ONE gap by asking a guiding question. Never state the missing
  idea, never give the correct answer, and never write or rewrite the
  student's answer for them, even in part.
- Give no score, grade, or level.
- End by suggesting they revisit: {revisit}.
- Use only physics that agrees with the REFERENCE NOTES."""


def _reference_notes(question: dict) -> str:
    """The tutor's notes for the pages this question points back to."""
    notes = [tutor.load_notes("shared")]
    for link in question["revisit"]:
        page_notes = tutor.NOTES_DIR / f"{link['page']}.md"
        if page_notes.is_file():
            notes.append(page_notes.read_text(encoding="utf-8").strip())
    return "\n\n".join(notes)


def _revisit_labels(question: dict) -> str:
    return "; ".join(link["label"] for link in question["revisit"])


def _student_work(question: dict, answer: str) -> str:
    return f"QUESTION: {question['text']}\n\nSTUDENT'S ANSWER: {answer}"


def _normalize(text: str) -> str:
    """Lower case with single spaces, so quotes match despite formatting."""
    return re.sub(r"\s+", " ", text).strip().lower()


# ---- no rubric --------------------------------------------------------------

def _guided_feedback(model: str, question: dict, answer: str) -> str:
    system = (
        "You give formative feedback on a student's written answer in an "
        "introductory primer on superposition. There is no rubric for this "
        "question, so respond to what the student actually wrote.\n\n"
        + WRITING_RULES.format(revisit=_revisit_labels(question))
        + "\n\nREFERENCE NOTES\n" + _reference_notes(question))
    return tutor.ask_text(model, system, _student_work(question, answer))


# ---- with a rubric ----------------------------------------------------------

def _rubric_schema() -> dict:
    """The JSON shape the model must return for the rubric check."""
    return {
        "type": "object",
        "properties": {
            "question_id": {"type": "string"},
            "key_ideas": {"type": "array", "items": {
                "type": "object",
                "properties": {"id": {"type": "string"},
                               "status": {"type": "string", "enum": list(STATUSES)},
                               "evidence": {"type": "string"}},
                "required": ["id", "status", "evidence"]}},
            "misconceptions": {"type": "array", "items": {
                "type": "object",
                "properties": {"id": {"type": "string"},
                               "evidence": {"type": "string"}},
                "required": ["id", "evidence"]}},
            "level": {"type": "string", "enum": list(LEVELS)},
        },
        "required": ["question_id", "key_ideas", "misconceptions", "level"],
    }


def _rubric_prompt(question: dict) -> str:
    ideas = "\n".join(f"- {i['id']}: {i['text']}"
                      + (" (advanced)" if i["advanced"] else "")
                      for i in question["key_ideas"])
    wrong = "\n".join(f"- {m['id']}: {m['text']}"
                      for m in question["misconceptions"]) or "- (none listed)"
    return f"""You check a student's written answer against a rubric. Reply
with JSON only.

KEY IDEAS
{ideas}

MISCONCEPTIONS TO LOOK FOR
{wrong}

HOW TO CHECK
- For every key idea, give "status": "present" if the student's answer
  expresses it (in any wording), otherwise "absent".
- For "present", "evidence" must be an exact quote copied word for word
  from the student's answer. For "absent", use an empty string.
- List a misconception only if the answer shows it, with an exact quote
  from the student's answer as evidence.
- Use only the ids listed above.
- "level": "beginning" (few or no key ideas), "developing" (some), or
  "proficient" (all the ideas not marked advanced).
- Judge only what is written. Do not credit ideas the student did not
  express."""


def clean_rubric(raw, question: dict, answer: str) -> tuple[dict, bool]:
    """
    Check the model's rubric result in code.

    Returns (cleaned result, invented). `invented` is True if the model
    quoted evidence that is not in the student's answer; such ideas are
    set to "absent". Raises ValueError if the result is the wrong shape.
    """
    if (not isinstance(raw, dict) or not isinstance(raw.get("key_ideas"), list)
            or not isinstance(raw.get("misconceptions", []), list)
            or raw.get("level") not in LEVELS):
        raise ValueError("rubric result has the wrong shape")

    said = _normalize(answer)
    invented = False

    def quoted(entry) -> str | None:
        """The entry's evidence if it truly appears in the answer."""
        evidence = entry.get("evidence")
        if not isinstance(evidence, str):
            return None
        quote = _normalize(evidence)
        # A scrap such as "is" or "e" appears in every answer and proves
        # nothing, so a quote needs at least two words, and it must match
        # whole words ("tate" is not found inside "state").
        if len(quote.split()) < 2:
            return None
        whole = r"(?<!\w)" + re.escape(quote) + r"(?!\w)"
        return evidence.strip() if re.search(whole, said) else None

    found = {}
    for entry in raw["key_ideas"]:
        if isinstance(entry, dict) and entry.get("status") == "present":
            found[entry.get("id")] = entry

    ideas = []
    for idea in question["key_ideas"]:      # only ids from the questions file
        entry, status, evidence = found.get(idea["id"]), "absent", ""
        if entry is not None:
            evidence = quoted(entry)
            if evidence is None:
                invented, evidence = True, ""
            else:
                status = "present"
        ideas.append({"id": idea["id"], "status": status, "evidence": evidence})

    known = {m["id"] for m in question["misconceptions"]}
    misconceptions = []
    for entry in raw.get("misconceptions", []):
        if isinstance(entry, dict) and entry.get("id") in known:
            evidence = quoted(entry)
            if evidence is None:
                invented = True
            else:
                misconceptions.append({"id": entry["id"], "evidence": evidence})

    return {"question_id": question["id"], "key_ideas": ideas,
            "misconceptions": misconceptions, "level": raw["level"]}, invented


def _rubric_check(model: str, question: dict, answer: str) -> dict | None:
    """
    Step 1: the checked rubric result, or None if the model failed twice.
    The check is run a second time if the first reply was unusable or
    quoted words the student never wrote.
    """
    result = None
    for _ in range(2):
        try:
            raw = tutor.ask_json(model, _rubric_prompt(question),
                                 _student_work(question, answer),
                                 _rubric_schema())
            result, invented = clean_rubric(raw, question, answer)
        except ValueError:
            continue                 # broken JSON or wrong shape: try again
        if not invented:
            break
    return result


def _stems(text: str) -> set:
    """Meaningful words, lower case, with a plural "s" removed."""
    words = (w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3)
    return {w[:-1] if w.endswith("s") else w for w in words}


def copies_rubric(text: str, question: dict, rubric: dict) -> bool:
    """
    True if the feedback states a key idea the student has NOT reached,
    which would give the answer away. Ideas the student already expressed
    may be echoed back.

    How it decides: each unreached idea is split into its parts (at
    semicolons). A part counts as given away when the feedback contains
    more than COPY_THRESHOLD of its meaningful words. Words from the
    question itself and from the revisit labels don't count, because good
    feedback has to use them.

    This is a word-matching check, so it is a safety net, not a guarantee:
    a rewording with different vocabulary gets through.
    """
    expected = _stems(question["text"])
    for link in question["revisit"]:
        expected |= _stems(link["label"])
    written = _stems(text)
    absent = {i["id"] for i in rubric["key_ideas"] if i["status"] == "absent"}

    for idea in question["key_ideas"]:
        if idea["id"] not in absent:
            continue
        for part in idea["text"].split(";"):
            words = _stems(part) - expected
            # Too few words to judge (one shared word would be 100%).
            if len(words) >= 3 and len(words & written) / len(words) > COPY_THRESHOLD:
                return True
    return False


def _writer_prompt(question: dict, rubric: dict) -> str:
    texts = {i["id"]: i for i in question["key_ideas"]}
    status = {i["id"]: i for i in rubric["key_ideas"]}

    strengths = [f'- {texts[i]["text"]} (their words: "{status[i]["evidence"]}")'
                 for i in status if status[i]["status"] == "present"]
    # Ask about an expected idea first; an advanced one only if none remain.
    gaps = sorted((texts[i] for i in status if status[i]["status"] == "absent"),
                  key=lambda idea: idea["advanced"])
    wrong = {m["id"]: m["text"] for m in question["misconceptions"]}
    shown = [f'- {wrong[m["id"]]} (their words: "{m["evidence"]}")'
             for m in rubric["misconceptions"]]

    return (
        "You write formative feedback for a student from the result of a "
        "rubric check on their answer.\n\n"
        "WHAT THE STUDENT ALREADY HAS\n"
        + ("\n".join(strengths) or "- (nothing from the rubric yet; find "
           "something genuine in their answer to credit)") + "\n\n"
        "THE GAP TO ASK ABOUT (for your eyes only; do NOT state it or "
        "paraphrase it; ask a question that leads toward it)\n"
        + (f"- {gaps[0]['text']}" if gaps else "- (none: invite them to "
           "explain one part more precisely)") + "\n\n"
        "MISCONCEPTIONS SHOWN (ask a question that tests the idea; do not "
        "just say it is wrong)\n" + ("\n".join(shown) or "- (none)") + "\n\n"
        + WRITING_RULES.format(revisit=_revisit_labels(question))
        + "\n\nREFERENCE NOTES\n" + _reference_notes(question))


def _fallback(rubric=None) -> dict:
    return {"text": FALLBACK_TEXT, "mode": "fallback", "rubric": rubric,
            "flagged": True}


def give_feedback(model: str, question: dict, answer: str) -> dict:
    """
    Feedback on one answer. Returns a dictionary:
        text     what to show the student
        mode     "guided" (no rubric), "rubric", or "fallback"
        rubric   the checked rubric result (kept for instructors; never
                 shown to students), or None
        flagged  True if the model failed and the neutral message was used

    Raises tutor.OllamaUnavailable if the model can't be reached; the page
    decides what to tell the student.
    """
    if not has_rubric(question):
        text = _guided_feedback(model, question, answer)
        if not text.strip():
            return _fallback()
        return {"text": text, "mode": "guided", "rubric": None, "flagged": False}

    rubric = _rubric_check(model, question, answer)
    if rubric is None:
        return _fallback()

    system = _writer_prompt(question, rubric)
    for _ in range(2):               # one retry if the answer is given away
        text = tutor.ask_text(model, system, _student_work(question, answer))
        if text.strip() and not copies_rubric(text, question, rubric):
            return {"text": text, "mode": "rubric", "rubric": rubric,
                    "flagged": False}
    return _fallback(rubric)
