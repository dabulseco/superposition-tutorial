# Superposition State Primer

An interactive Streamlit primer on superposition for undergraduate STEM
majors. It has four topics, a "Go deeper" page, three open questions with
feedback, and an AI tutor on every page.

Based on the *Superposition State Primer* created at **Spelman College**.
This version was developed with the **Institute for Future Intelligence**.

This is a demonstration version. It stores nothing a student does
(see "What is stored").

## Pages

| Page | What students do |
|---|---|
| Home | See how the four topics connect; ask general questions |
| 1 · Bits & Superposition | Measure a light switch and a spinning coin; slap 100 coins |
| 2 · Coupled Oscillators | Pull two weights on springs; watch two patterns combine; read a real Fourier transform |
| 3 · Electrons & Qubits | Set a qubit's mix, predict, measure 1x and 100x |
| Go deeper: Superposition vs. mixture | Run the experiment that tells a superposition from "one or the other, we just don't know which" |
| 4 · Phi-Bit Systems | Mix left and right waves on a chain of weights; shift their phase |
| Test Your Understanding | Answer three questions in their own words, get feedback, revise |
| My Journey | See and download what they did during this visit |

Every topic follows predict → observe → explain. Each topic page ends with
two quick-check questions and an "Ask your own questions" chat.

## Run it on your computer

```bash
conda activate superposition        # or: conda create -n superposition python=3.12
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

For the tutor and the feedback, install [Ollama](https://ollama.com), pull a
chat model (for example `ollama pull llama3.2`), and keep Ollama running.
Pick a model in the sidebar under "Tutor". The list matches `ollama list`,
and the top model is selected by default. Without Ollama every simulation
still works; the chat and feedback say they are off.

To use Ollama on another machine: `OLLAMA_URL=http://<host>:11434 streamlit run app.py`

## What is stored

Nothing. A student's predictions, answers, and questions are kept only in
their browser tab and disappear when it closes. The My Journey page lets
the student download the record as a web page or Markdown file.

There is one exception you control: on your own computer (not when hosted)
the sidebar has a checkbox, off by default, that saves tutor questions and
answers to `logs/tutor_log.jsonl`. Don't use it with students without an
approved research protocol.

Collecting student data for research (study codes, consent, a database, an
instructor dashboard) is designed in `superposition-primer-v2-spec.md` but
not built. It needs IRB approval first. `components/journey.py` is the one
place a saved record would be added.

## The tutor

The tutor guides rather than tells: it gives a hint, asks one directed
question, and offers "questions to consider next" as buttons. It is told
what the student currently sees on the page (slider values, predictions,
and, only after the student has run or measured, the results).

Holding back results is done by instructing the model, so how well it works
depends on the model. Try a few and pick one that follows instructions well.

To change how the tutor behaves, edit the prompt in `build_system_prompt()`
in `tutor.py`.

### Adding background for the tutor

The tutor's reference notes are plain Markdown files in `content/notes/`:

- `shared.md` is used on every page.
- `t1.md`, `t2.md`, `t3.md`, `t3b.md`, `t4.md` are used on the matching page.

Edit them, or add material (for example a study guide's instructions) to
`shared.md`. No code change is needed.

## Test Your Understanding: adding a rubric

The three questions are in `content/questions.yaml`. They ship **without a
rubric**. In that state, feedback names one strength in the student's
answer, asks one guiding question, and points to a simulation to revisit.
It never gives a grade and never writes the answer.

To add a rubric, fill in `key_ideas` (and optionally `misconceptions`) for a
question in `content/questions.yaml`, then restart the app:

```yaml
  - id: q1
    text: "What is a superposition state?"
    revisit:
      - {label: "Topic 3: the probability slider", page: t3}
    key_ideas:
      - {id: q1.k1, text: "A superposition is a combination of two basic states at once."}
      - {id: q1.k2, text: "Measuring gives just one of the basic states."}
      - {id: q1.k3, advanced: true, text: "The relative phase between the parts matters."}
    misconceptions:
      - {id: M-mixture, text: "It is secretly one state and we just don't know which."}
```

Once a question has key ideas, its feedback changes by itself:

1. The model checks the answer against each key idea and must quote the
   student's words as evidence.
2. Code verifies each quote is really in the answer. An idea "found" with an
   invented quote is not credited.
3. The model writes feedback from the checked result. Code rejects feedback
   that states a key idea the student hasn't reached, so the answer isn't
   handed over.

A draft rubric for all three questions is in
`content/questions.rubric-draft.yaml`. The app does not load it. Copy from
it what you want.

If the file has a mistake (a missing id, a duplicate, a page that doesn't
exist), the app shows a message naming the file and the problem.

## Quick checks

The two multiple-choice items at the end of each topic are in
`content/quick_checks.yaml`. Edit them there. To hide quick checks, replace
the file's contents with `items: []`.

## Page text

Titles, introductions, and "things to try" are in `content/pages.yaml`.
The wording follows the Spelman primer, with two changes: Topic 1 says
"in a combination" (was "experiencing a mix, or combination"), and Topic 3
says "in a combination of the two" (was "hovering in a mixed state between
the two"), because "mixed state" is the technical term for the opposite
idea. On Topic 4 the sliders are labeled as amplitude (was "Wave Power"),
with power shown as a readout.

## Host it online (Streamlit Community Cloud)

A web host has no Ollama of its own, so the hosted app uses Ollama's cloud
service. The app switches to this mode by itself when it finds an API key.
In this mode what students type in the chat and in the answer boxes **is
sent to Ollama's servers**; the app says so on the page.

1. Create a key at https://ollama.com/settings/keys
2. Push this folder to GitHub. The `.gitignore` keeps secrets and logs out.
3. At https://share.streamlit.io choose "Create app", pick the repository,
   set the main file to `app.py` and Python to 3.12.
4. Under "Advanced settings" > "Secrets", paste:

   ```toml
   OLLAMA_API_KEY = "your-key-here"
   APP_PASSWORD = "a-password-for-your-class"
   ```

5. Deploy, then share the link and the password.

Everyone can use the simulations. The tutor and the feedback ask for the
class password first, so strangers who find the link can't spend your
quota. Leave `APP_PASSWORD` out and they are open to anyone with the link.

Optional: `OLLAMA_MODELS = "gemma4:31b, gpt-oss:120b"` sets which cloud
models the sidebar offers (the first is the default).

To try hosted mode on your own computer first, copy
`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, fill it in,
and run the app. Never commit that file or put the key in the code.

## Code layout

```
app.py          the menu, the sidebar, and the footer
pages/          one file per page
physics/        the physics: no Streamlit, no language model
components/     pieces the pages share (chat, prediction gate, plots, journey)
content/        the words: page text, questions, quick checks, tutor notes
tutor.py        talking to the language model
feedback.py     reading the questions files; feedback on written answers
tests/          automated checks
```

Every number a student sees comes from the functions in `physics/`, never
from the language model. Each has a docstring giving its formula.

## Tests

```bash
pytest
```

The tests cover the physics (for example, the oscillator formula against a
direct solution of Newton's equations, and standing-wave nodes that don't
move), every page, the prediction lock, the feedback checks, and the
content files. They use a stand-in for Ollama, so Ollama doesn't need to be
running.
