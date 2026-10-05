# Superposition vs. Mixture

An interactive Streamlit simulation for undergraduate quantum mechanics.
It targets one well-documented misconception: that a superposition is
"secretly one state or the other" (a classical mixture).

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at http://localhost:8501.

## Ask the tutor (LLM via Ollama)

Students can type questions in the chat box at the bottom of the page.
By default, answers come from a model running on this computer through
[Ollama](https://ollama.com), so no student data leaves the machine.
(To put the app online instead, see "Host it online" below.)

1. Install Ollama and pull a chat model, e.g. `ollama pull llama3.2`
2. Keep Ollama running, then start the app.
3. Pick a model in the sidebar under "4. Tutor". The list matches
   `ollama list`, and the top model is selected by default.

The tutor is given the current slider settings, the student's prediction,
and short reference notes, so it answers about what is on screen. Until the
student runs the experiment, it is told not to give away the result for the
current axis. Embedding-only models (e.g. `nomic-embed-text`) appear in the
list but can't chat; the app says so if one is chosen.

Optional: tick "Save questions and answers to a local log file" to write
each exchange to `logs/tutor_log.jsonl`. Check your IRB protocol before
using this with students.

To use Ollama on another machine: `OLLAMA_URL=http://<host>:11434 streamlit run app.py`

## How the tutor teaches

The tutor guides rather than tells. When a student asks something they
could work out, it gives a hint or something to try in the simulation and
asks one directed question, building on what the student said and giving
credit for partial ideas. It answers directly for definitions and "how do I
use this page" questions, and gives the full explanation once a student has
made two real attempts or asks plainly to be told.

Under each answer the tutor offers two or three "questions to consider
next" as buttons; clicking one asks it. Before the first question, three
starter questions are shown (`STARTER_QUESTIONS` in `tutor.py`).

To change this behavior, edit the "GUIDE, DON'T TELL" and "QUESTIONS TO
CONSIDER NEXT" sections of the prompt in `build_system_prompt()`.

## Download the conversation

Once a student has asked a question, two buttons appear under the chat:
"Download as HTML" (a web page that opens in any browser) and "Download as
Markdown" (plain text that is easy to analyze). Each file records, for every
question, the time and the simulation settings on screen, and for every
answer, the model that wrote it.

## Host it online (Ollama cloud API key)

A web host has no Ollama of its own, so the hosted app uses Ollama's cloud
service instead. The app switches to this mode by itself when it finds an
API key. In this mode student questions ARE sent to Ollama's servers;
check your IRB protocol before using it with students.

1. Create a key at https://ollama.com/settings/keys
2. Put this folder in a GitHub repository. The included `.gitignore` keeps
   secrets and logs out of it.
3. At https://share.streamlit.io choose "Create app", pick the repository,
   and set the main file to `app.py`.
4. Under "Advanced settings" > "Secrets", paste:

   ```toml
   OLLAMA_API_KEY = "your-key-here"
   APP_PASSWORD = "a-password-for-your-class"
   ```

5. Deploy, then share the link and the password with your students.

Everyone can use the simulation. The tutor asks for the class password
first, so strangers who find the link can't spend your Ollama quota. If you
leave `APP_PASSWORD` out, the tutor is open to anyone with the link.

Optional: `OLLAMA_MODELS = "gemma4:31b, gpt-oss:120b"` sets which cloud
models the sidebar offers (the first is the default).

To try hosted mode on your own computer first, copy
`.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml`, fill it in, and run `streamlit run app.py`.
Never commit that file or put the key in the code.

The "save to a local log file" option is hidden when hosted, because a web
host wipes its files on restart. Use the download buttons instead.

## What students do

1. **Build** a state with two sliders (balance θ and relative phase φ).
   The app builds the matching mixture automatically.
2. **Choose** a measurement axis (z, x, y, or custom).
3. **Predict** whether the two states will give the same or different results.
4. **Observe** simulated shot-by-shot results against theory.
5. **Explain** using the P(+) sweep plot and the density matrices.

## Design notes for the agentic primer

The physics functions in Part 1 of `app.py` (`bloch_vector_pure`,
`bloch_vector_mixture`, `probability_plus`, `simulate_shots`,
`density_matrix`) have no Streamlit code in them. A simulation agent can
call them directly as tools, so every number a student sees comes from code
rather than from a language model.

`tutor.py` holds all the model code. Its `REFERENCE_NOTES` block is where
retrieved passages from the RAG corpus will go next.
