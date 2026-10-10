"""
components/chat_panel.py — the "Ask your own questions" chat on every page
==========================================================================

The model logic lives in tutor.py. This file is the part the student sees:
the model picker in the sidebar, the class password (when hosted), the chat
box, the suggested questions, and the download buttons.

Each page keeps its own conversation, so the tutor's answers stay about the
page the student is on.
"""

import hmac
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

import tutor
from components import journey

# Where Q&A is saved if logging is switched on in the sidebar (local only).
LOG_FILE = Path(__file__).parent.parent / "logs" / "tutor_log.jsonl"


def model_picker():
    """
    Sidebar dropdown of Ollama models.
    Local: the installed models; the default is the first one, i.e. the top
    line of `ollama list`. Hosted: the short list in tutor.HOSTED_MODELS.

    The choice is remembered in st.session_state so every page's chat (and
    the feedback on Test Your Understanding) uses the same model.
    Returns (model name or None, error message or None).
    """
    model, error = None, None
    with st.sidebar:
        st.subheader("Tutor")
        try:
            models = tutor.list_models()
        except tutor.OllamaUnavailable as err:
            models, error = [], str(err)

        if not models and error is None:
            error = ("The Ollama cloud service listed no models." if tutor.HOSTED else
                     "Ollama is running but has no models. Run `ollama pull llama3.2`, then reload.")

        if error:
            st.warning(error)
        elif tutor.HOSTED:
            model = st.selectbox("Model (Ollama cloud)", models, index=0,
                                 key="tutor_model_choice")
        else:
            model = st.selectbox("Model (installed in Ollama)", models, index=0,
                                 key="tutor_model_choice",
                                 help="Listed in the same order as `ollama list`.")

        if tutor.HOSTED:
            # A web host wipes its files on restart, so a log there would
            # be lost. Students download the conversation instead.
            st.session_state["save_log"] = False
        elif model:
            st.session_state["save_log"] = st.checkbox(
                "Save questions and answers to a local log file", value=False,
                help=f"Saved on this computer only, at {LOG_FILE}")

    st.session_state["tutor_model"] = model
    st.session_state["tutor_error"] = error
    return model, error


def tutor_unlocked(key: str) -> bool:
    """
    Ask for the class password, if one is set (APP_PASSWORD).
    Returns True once the student may use the tutor.
    """
    if not tutor.APP_PASSWORD or st.session_state.get("tutor_unlocked"):
        return True

    with st.form(f"tutor_password_{key}"):
        entered = st.text_input("Class password", type="password",
                                help="Ask your instructor for it.")
        submitted = st.form_submit_button("Unlock the tutor")

    if submitted:
        # compare_digest takes the same time whether or not the guess is close.
        if hmac.compare_digest(entered.encode(), tutor.APP_PASSWORD.encode()):
            st.session_state["tutor_unlocked"] = True
            st.rerun()
        st.error("That password is not right.")
    return False


def privacy_caption() -> str:
    """Who sees what the student types. Shown wherever text goes to the model."""
    if tutor.HOSTED:
        return ("What you type here is sent to Ollama's cloud service to be "
                "answered, so don't type personal information.")
    return "Answers come from a model running on this computer."


def _suggested_questions(key, chat, starters):
    """
    Buttons for questions to consider next. Before the first question these
    are the page's starters; afterwards the tutor proposes them with each
    answer. Clicking one asks it.
    """
    questions = chat[-1].get("suggestions", []) if chat else list(starters)
    if not questions:
        return

    def ask(question):
        st.session_state[f"clicked_question_{key}"] = question

    st.caption("Questions to consider next (click one to ask it):" if chat
               else "Not sure where to start? Try one of these:")
    for i, question in enumerate(questions):
        st.button(question, key=f"suggest_{key}_{len(chat)}_{i}",
                  on_click=ask, args=(question,))


def _download_buttons(key, chat, title):
    """Buttons that save the conversation as a web page or Markdown file."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    col_html, col_md, _ = st.columns([1, 1, 2])
    col_html.download_button(
        "Download as HTML", tutor.conversation_html(chat, title),
        file_name=f"tutor-conversation-{stamp}.html", mime="text/html",
        key=f"dl_html_{key}", help="A web page that opens in any browser.")
    col_md.download_button(
        "Download as Markdown", tutor.conversation_markdown(chat, title),
        file_name=f"tutor-conversation-{stamp}.md", mime="text/markdown",
        key=f"dl_md_{key}", help="Plain text that is easy to analyze later.")


def chat_panel(context: dict, starter_questions=(), seed_message: str | None = None,
               heading: str = "Ask your own questions") -> None:
    """
    Chat box where students ask questions about the page they are on.

    context           what the tutor is told about the page (see
                      tutor.build_system_prompt for the keys)
    starter_questions shown as buttons before the first question
    seed_message      if given, it is asked straight away as if the student
                      had typed it (used by "Discuss this question")
    """
    key = context.get("chat_key", context["page_id"])
    chat = st.session_state.setdefault(f"chat_{key}", [])
    model = st.session_state.get("tutor_model")

    st.divider()
    st.subheader(heading)
    st.caption(f"Ask about anything on this page. {privacy_caption()} "
               "Answers can be wrong, so check them against the simulation.")

    for msg in chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if model is None:
        reason = st.session_state.get("tutor_error") or "Ollama is not available."
        st.info(f"The tutor is off. {reason}")
        return

    if not tutor_unlocked(key):
        return

    # A question is typed, picked by clicking a suggestion, or seeded.
    typed = st.chat_input("Type your question here", key=f"chat_input_{key}")
    clicked = st.session_state.pop(f"clicked_question_{key}", None)
    question = typed or clicked or seed_message
    if question:
        # The time and settings are kept for the downloadable transcript.
        chat.append({
            "role": "user", "content": question,
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "settings": tutor.settings_text(context),
            "suggested": not typed,
        })
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                suggestions = []
                answer = st.write_stream(tutor.stream_answer(
                    model, tutor.build_system_prompt(context), chat, suggestions))
            except tutor.OllamaUnavailable as err:
                st.error(str(err))
                chat.pop()   # drop the unanswered question
                return

        chat.append({"role": "assistant", "content": answer, "model": model,
                     "suggestions": suggestions})
        journey.record("chat_question", context["page_id"],
                       question=question, answer=answer, model=model)
        if st.session_state.get("save_log"):
            tutor.log_interaction(LOG_FILE, model, context, question, answer)

    _suggested_questions(key, chat, starter_questions)

    if chat:
        _download_buttons(key, chat, f"{context['page_title']}: tutor conversation")
        if st.button("Clear conversation", key=f"clear_{key}"):
            st.session_state[f"chat_{key}"] = []
            st.rerun()
