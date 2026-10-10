# Superposition State Primer v2 — Build Plan

A working checklist for turning the current one-page app into the four-topic
primer. Tick boxes as you go. Each phase ends with something you can run.

**Spec:** `superposition-primer-v2-spec.md` (section numbers below, e.g. §5.2, point into it)

**Goal:** A multipage Streamlit primer (four topics, a "Go deeper" page, Test
Your Understanding, My Journey) with the Ollama tutor on every page, good
enough to demonstrate in a grant submission.

**Approach:** Keep the app at the repo root so `app.py` stays the Streamlit
entry point. Move physics into plain Python modules with tests, build each
topic as its own page on shared components (prediction gate, chat panel,
state card), and keep the student's journey in the browser session only.

**Stack:** Python 3.12, Streamlit ≥ 1.48 (`st.navigation`, `AppTest`), Plotly,
NumPy, requests, PyYAML, pytest. Conda env (never venv). Ollama locally;
Ollama cloud key when hosted.

---

## Decisions that shape this plan

These come from your instructions and change what the spec asks for.

| # | Your constraint | What the plan does |
|---|---|---|
| D1 | Grant demo, no IRB, no research yet | **Nothing a student does is stored by the app.** No study code, consent screen, hashed IDs, database, or instructor dashboard (§9, §10 deferred). The journey lives in the browser session and the student can download it. |
| D2 | Attribution to Spelman College and the Institute for Future Intelligence | One footer, drawn on every page from a single constant (Task 1.6). |
| D3 | No Gem instructions or knowledge files | Tutor notes are written from the spec (§2, §3.4, §5). They are plain Markdown files, so Gem material can be dropped in later without code changes. |
| D4 | Rubric added later, not from the UI | Rubrics live in `content/questions.yaml`. With no rubric, feedback runs in a "guiding question" mode. Add key ideas to the file and the rubric check (§8.3) switches on by itself. The rubric path is built and tested now against a test-only rubric. |
| D5 | Laptop pilot, then GitHub, then Streamlit Community Cloud | Phases 9 and 10. Local uses Ollama on the laptop; hosted uses the existing `OLLAMA_API_KEY` / `APP_PASSWORD` switch in `tutor.py`. |

Smaller choices made here (change any of them before starting the phase named):

- **Folder:** files stay at the repo root, not in a new `superposition_primer/` folder, so the existing GitHub repo and Streamlit Cloud setup keep working. (Phase 1)
- **No `config.yaml`:** settings stay in environment variables / Streamlit secrets as they are now. (Phase 1)
- **One conversation per page**, not one shared chat. (Task 1.4)
- **Journey download is HTML and Markdown**, matching the existing transcript download. No PDF library; print the HTML to PDF from the browser. (Phase 7)
- **The spec's draft rubrics (§8.2) are saved but not active**, in `content/questions.rubric-draft.yaml`, because the Spelman team has not approved them. (Task 6.1)
- **Quick checks (§8.4) are in**, built last of the features, using the spec's eight draft items. (Phase 8)

## Rules for every task

- Physics modules import no Streamlit and no model code. Every physics function has a docstring giving the formula and units.
- Every file starts with a plain-language docstring. Comments explain why. Keep functions short. (Existing house style.)
- Colors come from `components/theme.py` only. Keep the existing three: `#1f5fbf`, `#c98a00`, `#2e8b57`.
- Every animation has a pause control and a one-sentence text summary under it.
- Every page must work with Ollama switched off: simulation fully usable, chat shows "The tutor is off."
- The tutor is given results only after the student has run or measured.
- Reproduced labels and question wording match the Spelman site exactly (§2, §5), except for the five approved wording edits listed at the end of this plan. Reproduction is confirmed with Spelman.
- Credit Spelman College only. Do not name NewFoS anywhere in the app's text, notes, or README (the spec's §5.5 "Same and different" panel mentions it; leave that phrase out).
- In hosted mode, any box whose text goes to the model carries the "don't type personal information" caption, including the Test Your Understanding answer boxes.
- Write the test first, watch it fail, then write the code. Commit at the end of each task.

## Things most likely to go wrong (each has a test in the task named)

1. **Ollama off or dropping mid-answer** on any page, including while feedback is being written → student sees a clear message, their answer is kept, nothing crashes. (Tasks 1.4, 6.3)
2. **The model returns broken or off-format JSON** for the rubric check → one retry, then a neutral message and revisit link. (Task 6.2)
3. **`questions.yaml` edited by hand with a mistake** (missing id, duplicate id, bad indent) → the app names the file and the problem at startup instead of failing mid-page. (Task 6.1)
4. **Sliders at the ends:** both phi-bit amplitudes at 0 (division by zero in "share of State 1"), P(UP) at 0% or 100%, both oscillator weights at 0. (Tasks 3.1, 4.1, 5.1)
5. **Empty, whitespace-only, or very long answers** in Test Your Understanding → Submit is blocked for empty; long answers are capped at 4,000 characters with a visible counter. (Task 6.3)

---

## File map

```
app.py                         entry point: navigation, sidebar, footer
tutor.py                       existing; build_system_prompt generalized
feedback.py                    Test Your Understanding feedback (both modes)
requirements.txt  README.md  .gitignore  pytest.ini
physics/      mixture.py  bits.py  oscillators.py  qubit.py  phibit.py
pages/        home.py  t1_bits.py  t2_oscillators.py  t3_qubits.py
              t3b_superposition_vs_mixture.py  t4_phibits.py
              test_understanding.py  my_journey.py
components/   theme.py  plots.py  chat_panel.py  prediction_gate.py
              state_card.py  journey.py  layout.py
content/      pages.yaml  questions.yaml  questions.rubric-draft.yaml
              quick_checks.yaml  notes/{shared,t1_bits,t2_oscillators,
              t3_qubits,t3b_mixture,t4_phibits}.md
tests/        test_physics_*.py  test_tutor.py  test_feedback.py
              test_content.py  test_pages.py  fake_ollama.py
```

Not built: `data/store.py`, `data/schema.sql`, `instructor_app.py`, `config.yaml`, `components/session.py`.

---

## Phase 0 — Setup

- [ ] Confirm the conda env: `conda activate superposition` then `python -c "import streamlit; print(streamlit.__version__)"`. It must print 1.48 or later (the base env has 1.42, which is too old). If the env is stale, recreate it: `conda create -n superposition python=3.12 -y && conda activate superposition && pip install -r requirements.txt`.
- [ ] Add `pyyaml>=6.0` and `pytest>=8.0` to `requirements.txt`; `pip install -r requirements.txt`.
- [ ] Add `pytest.ini` with `testpaths = tests` and `pythonpath = .`.
- [ ] Run the current app once (`streamlit run app.py`) and ask the tutor one question, so you know the starting point works.
- [ ] Create a branch: `git checkout -b primer-v2`.
- [ ] Commit `superposition-primer-v2-spec.md` and `build_plan.md`.

## Phase 1 — Restructure into a multipage app (spec §4, §5.4, §7)

Result: the existing page runs as "Go deeper: Superposition vs. mixture" inside a multipage shell, with the footer, shared chat panel, and prediction gate.

### Task 1.1 — Move the mixture physics out of `app.py`
Files: create `physics/__init__.py`, `physics/mixture.py`, `tests/test_physics_mixture.py`; modify `app.py`.

- [ ] Write tests first: `probability_plus` for θ=90°, φ=0 gives 0.5 along z and 1.0 along x for the superposition, 0.5 along both for the mixture; mixture Bloch vector has zero x and y; `density_matrix` of the mixture has zero off-diagonals; `simulate_shots` is repeatable for a fixed seed.
- [ ] Move `unit_vector`, `bloch_vector_pure`, `bloch_vector_mixture`, `density_matrix`, `probability_plus`, `simulate_shots`, `describe_state` unchanged into `physics/mixture.py`.
- [ ] `pytest tests/test_physics_mixture.py -v` passes. Commit.

### Task 1.2 — Theme and shared plot helpers
Files: create `components/__init__.py`, `components/theme.py`, `components/plots.py`.

- [ ] `theme.py`: `COLOR_PURE`, `COLOR_MIX`, `COLOR_AXIS` (existing values) plus two more colorblind-safe colors for State 0 / State 1 and Pattern 1 / Pattern 2.
- [ ] `plots.py`: move `_arrow`, `bloch_sphere_figure`, `results_figure`, `sweep_figure`, `_matrix_latex` here. Add `bloch_sphere_base()` (sphere + axes only) so Topic 3 and the state card can reuse it.
- [ ] Commit.

### Task 1.3 — Generalize the tutor prompt
Files: modify `tutor.py`; create `content/notes/shared.md`, `content/notes/t3b_mixture.md`, `tests/test_tutor.py`.

Interface every page will use:

```python
# A page describes itself to the tutor with this dictionary.
context = {
    "page_id": "t3b",                       # also the notes file stem
    "page_title": "Superposition vs. mixture",
    "controls": "sliders for theta and phi, the measurement axis, ...",
    "settings_lines": ["theta = 90 deg, phi = 0 deg", ...],   # always sent
    "results_lines": ["Theory: P(+) superposition = 1.000", ...],  # sent only if revealed
    "revealed": False,                      # True once the student has run/measured
    "hold_back": "the probabilities for the current axis",   # what not to give away
}
tutor.build_system_prompt(context) -> str
tutor.load_notes(page_id) -> str   # shared.md + <page_id>.md; missing file = ""
tutor.settings_text(context) -> str   # "; ".join(settings_lines) + run status
```

- [ ] Tests first: prompt contains every settings line; contains results lines only when `revealed`; contains the "has NOT run" rule and the `hold_back` text when not revealed; contains the notes for the page and the shared notes; a missing notes file does not raise; existing `hide_thinking` and `split_suggestions` behave as now (tag split across pieces, decorated marker).
- [ ] Move the current `REFERENCE_NOTES` text into `content/notes/t3b_mixture.md`.
- [ ] Write `content/notes/shared.md` from spec §3.1 and §3.4: the one-story thread; "mixed state" means a classical mixture; where the coin analogy breaks; amplitude vs. power.
- [ ] Rewrite `build_system_prompt` to take `context`. Keep the HOW TO ANSWER, GUIDE DON'T TELL, and NEXT QUESTIONS sections word for word. Add the two rules from §7.3: unsure → say so; off-topic → one sentence, then steer back.
- [ ] Update `log_interaction` and `settings_text` to the new dictionary.
- [ ] `pytest tests/test_tutor.py -v` passes. Commit.

### Task 1.4 — Shared chat panel
Files: create `components/chat_panel.py`, `tests/fake_ollama.py`; add to `tests/test_tutor.py`.

Interface: `chat_panel(context, starter_questions, seed_message=None)` and `model_picker() -> (model | None, error | None)`. The conversation is stored under `st.session_state[f"chat_{page_id}"]`.

- [ ] Move `tutor_model_picker`, `tutor_unlocked`, `suggested_questions`, `download_buttons`, `tutor_chat` from `app.py` into `chat_panel.py`, switched to the `context` dictionary. Rename the heading to "Ask your own questions" (§7.1).
- [ ] `seed_message`: when given, it is sent as the first student message (used later by "Discuss this question").
- [ ] `tests/fake_ollama.py`: a small local HTTP server answering `/api/tags` and `/api/chat` (streamed lines), with switches for "no models", "error 500", and "connection drops mid-stream".
- [ ] Tests against the fake server: model list order and default; streaming; `<think>` hidden; a 500 gives `OllamaUnavailable` with the embedding-model hint; a dropped connection gives `OllamaUnavailable` and does not leave a half answer in the history.
- [ ] Commit.

### Task 1.5 — Prediction gate
Files: create `components/prediction_gate.py`; test in `tests/test_pages.py` (Task 1.7).

Interface:

```python
gate = prediction_gate(key, signature)   # signature = tuple of the settings that matter
choice = gate.ask_choice(question, options)      # or gate.ask_number(question, lo, hi)
if gate.run_button("Run the experiment"):        # True while results should show
    ...
gate.prediction     # the student's prediction, or None
gate.ran            # True after Run, until the signature changes
```

- [ ] When `signature` differs from the one saved at the last run, clear `ran` **and** reset the prediction, and show "Settings changed. Make a new prediction to run again." This is the fix called for in §5.4.
- [ ] Commit.

### Task 1.6 — App shell: navigation, sidebar, footer
Files: rewrite `app.py`; create `components/layout.py`, `pages/home.py`, `content/pages.yaml`.

- [ ] `app.py`: `st.set_page_config`, `tutor.load_settings()`, build pages with `st.Page` and `st.navigation` in this order: Home; 1 Bits & Superposition; 2 Coupled Oscillators; 3 Electrons & Qubits; Go deeper: Superposition vs. mixture; 4 Phi-Bit Systems; Test Your Understanding; My Journey. Pages not built yet show "Coming in a later phase."
- [ ] Sidebar (§4.2, minus study code and consent): progress list (topics visited, questions answered) and the tutor model picker. Keep the existing "Save questions and answers to a local log file" checkbox, local only and off by default.
- [ ] `layout.py`: `page_header(page_id)` (title + intro from `pages.yaml`), `prev_next(page_id)` buttons, and `footer()`.
- [ ] Footer text, kept in one constant `ATTRIBUTION` in `layout.py` so you can reword it in one place:
  > Based on the *Superposition State Primer* created at **Spelman College**. This version was developed with the **Institute for Future Intelligence**. Demonstration version: nothing you type is stored by this app.

  In hosted mode the last sentence becomes: "Demonstration version: questions and answers are sent to Ollama's cloud service to be answered and are not stored by this app."
- [ ] `content/pages.yaml`: for each page, `title`, `intro`, `things_to_try`, `starter_questions`. Copy titles and intros from the Spelman site (https://sites.google.com/view/newfos-primer-superposition/home); button and preset labels are already in spec §2.1.
- [ ] Apply the two text edits while copying: Topic 3 intro "hovering in a mixed state between the two" → "in a combination of the two"; Topic 1 "experiencing a mix" → "a combination". Add a `tests/test_content.py` check that no intro in `pages.yaml` contains "mixed state" or "experiencing a mix".
- [ ] `pages/home.py`: the one-story overview (§3.1), links to the four topics, and a general chat (`page_id="home"`, replaces the "Launch Gem" button).
- [ ] Commit.

### Task 1.7 — Move the existing page into "Go deeper"
Files: create `pages/t3b_superposition_vs_mixture.py`, `tests/test_pages.py`.

- [ ] Move `main()`'s page body here. Build-the-state and measurement controls move from the sidebar into the page's right-hand column (the sidebar is now shared).
- [ ] Replace the hand-rolled predict/run logic with `prediction_gate`, signature `(theta, phi, m_polar, m_azim, n_shots, seed)`.
- [ ] Add the short intro linking back to the Topic 1 coin and the Topic 3 slider (§5.4).
- [ ] Use `chat_panel` with a `tutor_context()` function returning the dictionary from Task 1.3.
- [ ] `AppTest` tests: page loads with Ollama off; Run is locked until a prediction is chosen; after Run, changing θ re-locks and clears the prediction; footer text is present.
- [ ] Run the app by hand and compare numbers with the old page for θ=90°, φ=0, along x: superposition P(+) = 1.000, mixture 0.500.
- [ ] `pytest -v` all green. Commit.

## Phase 2 — Topic 1: Bits & Superposition (§5.1, §6.1)

### Task 2.1 — Physics
Files: create `physics/bits.py`, `tests/test_physics_bits.py`.

- [ ] Tests first: `measure_classical("ON")` returns `"ON"` in 1,000 calls; `slap_coins(10000, seed)` lands within 4 standard errors (±200) of 5,000 heads for at least 999 of seeds 0–999; heads + tails = n; same seed gives the same result; `slap_coins(0, seed)` returns `(0, 0)`.
- [ ] Implement `measure_classical(state) -> str` and `slap_coins(n, seed, p_heads=0.5) -> (heads, tails)`. Commit.

### Task 2.2 — Page
Files: create `pages/t1_bits.py`, `content/notes/t1_bits.md`; add to `tests/test_pages.py`.

- [ ] Left: light switch with ON/OFF toggle and "Measure Classical Bit". Right: coin with "Measure Coin (Slap it down!)" → HEADS or TAILS, then "Reset (Spin Again)".
- [ ] "Measure 100 coins" with a running heads/tails tally and bar chart.
- [ ] Two predictions through the gate: switch measured 10 times → how many ON; 100 coin slaps → about how many heads. Show the actual count and the difference.
- [ ] "Where the analogy breaks" expander with a link to the Go deeper page.
- [ ] `tutor_context()`: switch state, coin state, tallies (tallies only after measuring).
- [ ] Notes file: classical bit vs. coin, 50/50 statistics, the limit of the coin analogy.
- [ ] `AppTest`: toggle then measure reports the set state; coin measure then reset; 100-coin tally adds to 100; works with Ollama off.
- [ ] Commit.

## Phase 3 — Topic 2: Coupled Oscillators (§5.2, §6.2)

### Task 3.1 — Physics
Files: create `physics/oscillators.py`, `tests/test_physics_oscillators.py`.

- [ ] Tests first:
  - `normal_modes(1, 2.625, 1)` gives ω = 1.0 and 2.5 to 1e-9, vectors (1,1)/√2 and (1,−1)/√2 (compare up to sign).
  - `mode_amplitudes(40, 40) == (40, 0)`; `(40, −40)` → `(0, 40)`; `(40, 0)` → `(20, 20)`; `(0, 0)` → `(0, 0)`.
  - `positions` matches a direct numerical solution of Newton's equations (velocity-Verlet, dt = 1e-3, 30 time units) to 1e-6.
  - `spectrum` of x₁(t) for (40, −10) has peaks at ω = 1.0 and 2.5 with heights 15 and 25 (to 1%).
  - `random_start(seed)` never returns |x₁| = |x₂|, for seeds 0–999.
- [ ] Implement `normal_modes(k, k_c, m)`, `mode_amplitudes(x1_0, x2_0)`, `positions(t, x1_0, x2_0, k, k_c, m)`, `spectrum(trace, dt)`, `random_start(seed)`.
- [ ] For `spectrum`: sample over a whole number of the 4π repeat time so both default peaks land exactly on a frequency bin; when k_c is changed (Go deeper), zero-pad and read the peak nearest each mode frequency.
- [ ] Commit.

### Task 3.2 — State card
Files: create `components/state_card.py`; test in `tests/test_pages.py`.

- [ ] `state_card(amp0, amp1, phase_deg, labels)`: two amplitude bars and a mini Bloch sphere dot at θ = 2·arctan2(|amp1|, |amp0|), φ = phase. Both amplitudes zero → show "No state yet" instead of a dot.
- [ ] Commit.

### Task 3.3 — Page
Files: create `pages/t2_oscillators.py`, `content/notes/t2_oscillators.md`.

- [ ] Sliders for both weights (Left 80 to Right 80, default Right 40 each). Presets "Pattern 1 Only (Both Right)", "Pattern 2 Only (Opposite)", "Random Superposition (Mix!)".
- [ ] Animation: Plotly frames, about 12 s loop, about 200 points, zigzag springs, circle weights, play and pause. Add `spring_trace` and `mass_trace` helpers to `components/plots.py`.
- [ ] Plots: weight 1 position over time; frequency spectrum from `spectrum()` with peaks labeled Pattern 1 and Pattern 2.
- [ ] Prediction: "With weight 1 at Right 40 and weight 2 at center, which patterns will light up?"
- [ ] "Go deeper" expander: coupling-strength slider k_c; Pattern 2's peak moves, Pattern 1's stays.
- [ ] State card with A₁, A₂.
- [ ] `tutor_context()` and notes file (normal modes, why two patterns, what the spectrum shows).
- [ ] `AppTest`: each preset sets the sliders; Pattern 1 preset shows A₂ = 0; works with Ollama off.
- [ ] Commit.

## Phase 4 — Topic 3: Electrons & Qubits (§5.3, §6.3)

### Task 4.1 — Physics
Files: create `physics/qubit.py`, `tests/test_physics_qubit.py`.

- [ ] Tests first: `theta_from_probability` gives 90° at 0.5, 0° at 1.0, 180° at 0.0; `measure(p, 10000, seed)` UP count within 4 standard errors of 10000·p for p = 0.1, 0.5, 0.7; `measure(1.0, 100, s) == (100, 0)` and `measure(0.0, 100, s) == (0, 100)`; ups + downs = n.
- [ ] Implement `theta_from_probability(p_up) -> theta_deg` and `measure(p_up, n, seed) -> (ups, downs)`. Commit.

### Task 4.2 — Page
Files: create `pages/t3_qubits.py`, `content/notes/t3_qubits.md`.

- [ ] Bloch-sphere arrow (reuse `bloch_sphere_base`); slider 100% DOWN to 100% UP, default 50/50.
- [ ] "Measure 1x" (arrow snaps to UP or DOWN), "Measure 100x" (adds 100 results, resets the arrow), results bars with counts, "Clear Data".
- [ ] Prediction before "Measure 100x": about how many UP out of 100; show actual and difference.
- [ ] "Sample size" note with a small chart of measured fraction vs. number of measurements.
- [ ] State card; link button to "Go deeper: Superposition vs. mixture".
- [ ] `tutor_context()` and notes file (amplitudes vs. probabilities, measurement snaps the state, repeat measurement gives the same result).
- [ ] `AppTest`: counts add up after 1x and 100x; Clear Data zeroes them; slider at 100% UP gives only UP; works with Ollama off.
- [ ] Commit.

## Phase 5 — Topic 4: Phi-Bit Systems (§5.5, §6.4)

### Task 5.1 — Physics
Files: create `physics/phibit.py`, `tests/test_physics_phibit.py`.

- [ ] Tests first:
  - `displacement` with δ = 0 equals a_L·cos(kx + ωt) + a_R·cos(kx − ωt) on a grid of x and t.
  - With a_L = a_R, displacement equals 2a·cos(kx + δ/2)·cos(ωt − δ/2) (to 1e-12), so nodes do not move in time.
  - `node_positions` shift by δ/(2k) when δ changes; every returned node has zero displacement at three different times.
  - `bloch_from_amplitudes(0.8, 0.6, 0)` → θ ≈ 73.74°, φ = 0; `share_of_state_1(0.8, 0.6) == 0.36`.
  - `classify` returns the five original labels: (100, 0) → Pure State 0; (0, 100) → Pure State 1; (100, 100) → 50/50 Superposition (Standing Wave); (100, 40) → Uneven Mix; (0, 0) → no waves.
  - Both amplitudes zero: `share_of_state_1` and `bloch_from_amplitudes` return `None`, no divide-by-zero warning.
  - Chain dispersion: the 12 numerical normal-mode frequencies of a chain (masses m, neighbor springs K, side springs k₀) all fall inside the band k₀/m ≤ ω² ≤ k₀/m + 4K/m.
- [ ] Implement `displacement`, `classify`, `bloch_from_amplitudes` (use `arctan2`), `share_of_state_1`, `node_positions`, `chain_dispersion(q, m, K, k0, a)`, `chain_modes(n, m, K, k0)`.
- [ ] Commit.

### Task 5.2 — Page
Files: create `pages/t4_phibits.py`, `content/notes/t4_phibits.md`.

- [ ] Chain of 12 weights with side springs and driver; displacement graph with colored dots under each weight; animation with play and pause.
- [ ] Presets "State 0 (100% Left)", "State 1 (100% Right)", "Superposition (Both!)"; "Driving Force Frequency (Motor Speed)" slider (default 1.5); Wave Mixer with LEFT and RIGHT sliders; status box from `classify`.
- [ ] Wave Mixer sliders labeled "LEFT Wave Amplitude" and "RIGHT Wave Amplitude" (replacing the site's "Wave Power"), with readouts for power (amplitude squared) and "share of State 1" (§3.4).
- [ ] Relative phase slider δ (0–359°, default 0) with the prediction: "If you change the phase while the mix is 50/50, what happens to the still points?"
- [ ] State card with the phi-bit state; "Same and different" panel (qubit vs. phi-bit).
- [ ] "Go deeper" toggle: real chain frequency–wavelength relation; below the lowest allowed frequency show "No traveling wave at this frequency."
- [ ] `tutor_context()` and notes file (two traveling waves as basis states, standing wave, phase moves the nodes, classical analog of a qubit and where it differs).
- [ ] `AppTest`: each preset gives the matching status label; both sliders at 0 shows the "no waves" status and no error; works with Ollama off.
- [ ] Commit.

## Phase 6 — Test Your Understanding (§8, changed by D4)

### Task 6.1 — Questions file and loader
Files: create `content/questions.yaml`, `content/questions.rubric-draft.yaml`, `tests/test_content.py`; start `feedback.py`.

`content/questions.yaml` as shipped (no rubric yet):

```yaml
# To add a rubric: fill in key_ideas and misconceptions for a question,
# save, and restart the app. No code change is needed. See README.
questions:
  - id: q1
    text: "What is a superposition state?"
    revisit:
      - {label: "Topic 3: probability slider", page: t3}
      - {label: "Go deeper: Superposition vs. mixture", page: t3b}
    key_ideas: []          # each: {id: q1.k1, text: "...", advanced: false}
    misconceptions: []     # each: {id: M-mixture, text: "..."}
  - id: q2
    text: "How does a physical phi-bit represented by a spring-mass chain demonstrate a superposition state?"
    revisit:
      - {label: "Topic 4: Superposition preset", page: t4, preset: superposition}
    key_ideas: []
    misconceptions: []
  - id: q3
    text: "What are the differences and similarities between a qubit and a coin resting on a table?"
    revisit:
      - {label: "Topic 1: Bits & Superposition", page: t1}
      - {label: "Topic 3: Electrons & Qubits", page: t3}
    key_ideas: []
    misconceptions: []
```

- [ ] Tests first: the shipped file loads and has exactly the three question texts above; `has_rubric(q)` is False for all three; the draft file loads and `has_rubric` is True for all three; a file with a duplicate id, a missing `text`, a key idea without `id`, or a `revisit.page` that is not a real page raises `ContentError` whose message names the file and the problem.
- [ ] `feedback.load_questions(path) -> list[dict]` and `feedback.has_rubric(question) -> bool`.
- [ ] Copy the §8.2 draft key ideas and misconceptions into `questions.rubric-draft.yaml` in the same format, with a header comment: "Draft, not approved by the Spelman team. Not loaded by the app."
- [ ] `app.py` calls `load_questions` at startup and shows any `ContentError` with `st.error` instead of a traceback.
- [ ] Commit.

### Task 6.2 — Feedback engine (both modes)
Files: finish `feedback.py`; create `tests/test_feedback.py`; add `tutor.ask_json(model, system, user, schema)` and `tutor.ask_text(...)` (non-streaming calls).

Interface: `feedback.give_feedback(model, question, answer) -> {"text": str, "mode": "guided" | "rubric" | "fallback", "rubric": dict | None, "flagged": bool}`

- [ ] Tests first, using the fake Ollama server with scripted replies:
  - No rubric → one model call, `mode == "guided"`.
  - With the test rubric → two calls, `mode == "rubric"`, checked JSON returned.
  - Evidence that is not in the student's answer (ignoring case and spacing) → that idea becomes "absent" and the check runs once more.
  - Unknown key-idea or misconception ids are dropped; `level` outside beginning / developing / proficient is rejected.
  - Reply that is not valid JSON → one retry → then `mode == "fallback"`, `flagged == True`.
  - Feedback text that copies rubric wording (word overlap with any key idea above 0.6) → one retry → then fallback.
  - `OllamaUnavailable` is passed up to the page untouched.
- [ ] Guided mode prompt: 3–5 sentences; one specific strength quoting the student's words; one gap phrased as a guiding question; never write or rewrite the answer; point to one of the question's revisit links.
- [ ] Rubric mode: step 1 structured output with Ollama's `format` JSON schema (§8.3), code checks, step 2 feedback text from the checked JSON. No score or level in the text.
- [ ] Fallback text: "Thanks for your answer. Try revisiting the simulation below, then revise your answer." plus the revisit link.
- [ ] Commit.

### Task 6.3 — Page
Files: create `pages/test_understanding.py`; add to `tests/test_pages.py`.

- [ ] For each question: text box (draft kept while moving between questions), optional confidence 1–5, Submit.
- [ ] Each submission is appended as a numbered attempt in `st.session_state["tyu_attempts"]`; earlier attempts are never overwritten and are shown in an expander.
- [ ] After Submit: spinner, then feedback, then revisit buttons. A revisit button sets the target page's preset in session state and calls `st.switch_page`.
- [ ] "Discuss this question" opens `chat_panel` with `seed_message` = question + latest answer, and a context whose `hold_back` is "a model answer to this question".
- [ ] Submit is disabled for empty or whitespace-only text; answers are capped at 4,000 characters with a counter.
- [ ] If Ollama is off or fails mid-feedback: the attempt is still saved, and the student sees "Your answer is saved. Feedback is unavailable right now."
- [ ] Hosted mode: the "don't type personal information" caption above the answer boxes.
- [ ] `AppTest`: submit → attempt 1 saved with feedback; submit again → attempt 2, attempt 1 unchanged; empty answer cannot be submitted; Ollama off → attempt saved, message shown.
- [ ] Commit.

## Phase 7 — My Journey, session only (§5.7, changed by D1)

Files: create `components/journey.py`, `pages/my_journey.py`; add `journey.record(...)` calls to pages; add to `tests/test_pages.py`.

Interface: `journey.record(event_type, page, **details)`, `journey.events() -> list[dict]`, `journey.to_markdown() -> str`, `journey.to_html() -> str`. Everything is kept in `st.session_state["journey"]`. This is the one place a saved store could be added later, after IRB approval.

- [ ] `record` calls on each page for: page visit, preset, measure / run, prediction (with whether it matched), Test Your Understanding submit, revisit link, chat question. Slider values are recorded with the measure / run event, not on every drag.
- [ ] `pages/my_journey.py`: a timeline grouped by page; predictions with match / no match; each answer with its attempts and feedback; chat questions. Banner at the top: "This record exists only in this browser tab. Download it to keep it."
- [ ] "Download as HTML" and "Download as Markdown" (all text escaped in the HTML, as in `tutor.conversation_html`).
- [ ] Sidebar progress list reads from `journey.events()`.
- [ ] Tests: events appear in order; the Markdown contains a submitted answer and its feedback; the HTML escapes `<script>` typed into an answer; nothing is written to disk (`logs/` not created) unless the local log checkbox is ticked.
- [ ] Commit.

## Phase 8 — Quick checks (§8.4)

The items are the spec's drafts. They live in `content/quick_checks.yaml`, so they can be edited there later; an empty file hides the feature.

- [ ] `content/quick_checks.yaml`: the eight items from §8.4, each with feedback for every wrong option and a revisit link.
- [ ] `components/quick_check.py`: shows a page's items at the end of the topic page; records to the journey.
- [ ] Loader test (same error rules as `questions.yaml`) and one `AppTest` per topic page.
- [ ] Commit.

## Phase 9 — Pilot on the laptop

- [ ] `pytest -v`: everything green.
- [ ] Rewrite `README.md`: what the primer is, how to run it, the page list, how to add a rubric (edit `content/questions.yaml`; the format; where the draft is), how to add tutor notes or Gem material later (drop Markdown into `content/notes/`), what is and is not stored, hosting steps, attribution.
- [ ] Ollama running, `streamlit run app.py`. Walk through as a student, start to finish:
  - [ ] Topic 1: both predictions, measure, 100 coins, analogy note.
  - [ ] Topic 2: three presets, prediction, Go deeper slider; the spectrum peaks match the state card bars.
  - [ ] Topic 3: predict, Measure 1x / 100x, Clear Data, open Go deeper.
  - [ ] Go deeper: predict, run, change θ, confirm it re-locks.
  - [ ] Topic 4: three presets, phase slider at 50/50 (nodes slide), both sliders at 0.
  - [ ] Ask the tutor one question per page; before running, confirm it does not give the result away.
  - [ ] Test Your Understanding: answer all three, revise one, follow a revisit link, use "Discuss this question" and ask it to write the answer for you (it should decline).
  - [ ] My Journey: check the timeline; download both files and open them.
- [ ] Quit Ollama and reload: every simulation still works; chat and feedback show clear "off" messages.
- [ ] Rubric switch test: copy the q1 block from `questions.rubric-draft.yaml` into `questions.yaml`, restart, submit a q1 answer, confirm feedback still reads well; then revert the file.
- [ ] Try two or three local models in the picker; note which gives usable feedback, and how long feedback takes (target under 15 s).
- [ ] Accessibility pass: keyboard-only through one topic; every animation has pause and a text summary; check the colors with a colorblind simulator.
- [ ] Hosted mode on the laptop: fill in `.streamlit/secrets.toml` (key + password), run, confirm the cloud model list, the password gate, the privacy captions, and that rubric-mode structured output works with the cloud model. Then remove the key again.
- [ ] Fix what you found. Commit.

## Phase 10 — GitHub, then Streamlit Community Cloud

- [ ] `git status`: confirm `.streamlit/secrets.toml`, `logs/`, and `zz-files/` are not staged.
- [ ] Merge `primer-v2` into `main` and push to `origin` (`github.com/dabulseco/superposition-tutorial`).
- [ ] At https://share.streamlit.io: point the app at `main` / `app.py`, Python 3.12. In Secrets set `OLLAMA_API_KEY`, `APP_PASSWORD`, and optionally `OLLAMA_MODELS`.
- [ ] Check the hosted app: all pages load; navigation and revisit links work; the tutor asks for the password; feedback works; My Journey downloads work; footer and hosted privacy wording show.
- [ ] Open it in a second browser and confirm the two sessions do not share answers or chat.
- [ ] Check on a phone-width window that the pages are still usable.
- [ ] Let the app go to sleep (or reboot it from the dashboard) and confirm it wakes cleanly with an empty journey.

---

## Deferred until there is IRB approval or a campus server

| Spec item | Section | Why deferred |
|---|---|---|
| Study code, consent, hashed IDs | §9.1–9.2 | No IRB protocol or consent text yet |
| SQLite database of events, attempts, chat | §9.3 | Same; also Streamlit Community Cloud wipes local files |
| Instructor dashboard and CSV export | §10 | Nothing stored to show |
| Rubric scores kept for research; feedback review queue | §8.3, §10 | Needs stored data |
| Feedback-quality study (85% agreement with a physicist) | §12 | Needs an approved rubric |
| Class mode, feedback on/off for pre-tests | §4.2, §8.1 | No classes yet |
| Campus server, Google Site embed, load test | §11 | After the grant |
| Reusing the Gem's instructions | §7.2, §14.2 | Not available |

## Open items for you (none of these block the build)

- [x] Footer credits Spelman College and the Institute for Future Intelligence only (no NewFoS).
- [x] Spelman has confirmed the primer's text and three questions may be reproduced.
- [x] Phase 8 (quick checks) is in.
- [x] All five wording edits from spec §3.4 are approved (table below).

### Approved wording edits (from spec §3.4)

| Where | Spelman site wording or behavior | Why it changes | What the app does | Task |
|---|---|---|---|---|
| Topic 3 intro | "hovering in a **mixed state** between the two" | "Mixed state" is the technical term for a classical mixture, the opposite idea (and the subject of the Go deeper page) | "in a **combination** of the two" | 1.6 |
| Topic 1 | "experiencing a **mix**" | Same ambiguity, milder | "a combination" | 1.6 |
| Topic 1 coin analogy | Spinning coin = superposition | A spinning coin's outcome is set by ordinary physics we just can't track, which is closer to a mixture. It has no phase and no interference | Keeps the analogy; adds a "Where the analogy breaks" note linking to Go deeper | 2.2 |
| Topic 4 sliders | Labeled "Wave **Power**" but used as **amplitude** | Power grows with amplitude squared. The qubit slider is a probability (also a square) | Labeled as amplitude; power and "share of State 1" shown as readouts | 5.2 |
| Topic 4 frequency | Slider changes only animation speed | In a real chain, frequency sets wavelength, and there is a lowest frequency that can travel | "Go deeper" toggle using the real frequency–wavelength relation | 5.2 |
