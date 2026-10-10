# Superposition State Primer, Version 2 — Brainstorm and Build Spec

*Spec for extending the existing Streamlit app (`superposition_vs_mixture/`)
into a four-topic primer that reproduces the Spelman College NewFoS
"Superposition State Primer" site, adds a locally hosted chatbot on every
page, and records each student's learning journey.*

*Version 0.1 — October 9, 2026. Separate from the future Quantum Foundations
Primer Series (see `quantum-primer-series-plan.md`), but built so it can fold
into that series later as its first primer.*

---

## 1. Why this version exists

The Spelman team's primer
(https://sites.google.com/view/newfos-primer-superposition/home) is a strong,
student-friendly introduction to superposition across four topics. Its
"Test your understanding" questions and its "Ask your own questions" help both
run through a Google Gemini Gem. That has one serious limitation for research:
**nothing the students write or ask is captured**. Answers are copied to the
clipboard and pasted into a Gem conversation that the team cannot retrieve,
so there is no record of how a student's understanding develops.

Version 2 keeps the Spelman primer's content and teaching sequence and changes
three things:

1. **The chatbot runs locally** (Ollama), on the same machine or a campus
   server, and sees what the student is looking at.
2. **"Test your understanding" happens inside the app.** Answers, revisions,
   feedback, and follow-up questions are saved.
3. **The learning journey is recorded** (with consent): which simulations a
   student used, what they predicted, how their answers changed, and what
   they asked.

---

## 2. What the Spelman site contains (inventory)

The site has a header image, two embedded HTML blocks, and a link to a Gem.

### 2.1 Primer embed: four tabs

| Tab | What students see and do | How it works (from the page code) |
|---|---|---|
| **1. Bits & Superposition** | A classical bit (light switch ON/OFF, "Measure Classical Bit") beside a spinning coin ("Measure Coin (Slap it down!)" → HEADS or TAILS, then "Reset (Spin Again)") | Switch toggles a definite state; measuring reports it. Coin gives 50/50 random result on measurement |
| **2. Coupled Oscillators** ("Jiggling Springs") | Two weights between walls connected by springs. Sliders set initial positions (Left 80 to Right 80, default Right 40 each). Presets: "Pattern 1 Only (Both Right)", "Pattern 2 Only (Opposite)", "Random Superposition (Mix!)". Plots: position of weight 1 over time, and a "Fourier Transform" bar chart showing which patterns are playing | Normal-mode formula with fixed frequencies ω₁ = 1.0 and ω₂ = 2.5. Mode amplitudes A₁ = (x₁ + x₂)/2 and A₂ = (x₁ − x₂)/2. x₁(t) = A₁cos ω₁t + A₂cos ω₂t; x₂(t) = A₁cos ω₁t − A₂cos ω₂t. Bar heights are \|A₁\|/80 and \|A₂\|/80 (drawn, not computed by a Fourier transform). Random preset avoids \|x₁\| = \|x₂\| |
| **3. Electrons & Qubits** | An arrow on a Bloch sphere. Slider from 100% DOWN to 100% UP (default 50/50). "Measure 1x" (arrow snaps to UP or DOWN) and "Measure 100x" (adds 100 results, resets arrow). Results bars with counts and "Clear Data" | θ = 2·arccos(√P_up), φ = 0 always. Each measurement is UP with probability P_up |
| **4. Phi-Bit Systems** ("Sound-like Waves") | A chain of 12 weights, each tied to a wall by a side spring and to its neighbors, driven at one end. Presets: "State 0 (100% Left)", "State 1 (100% Right)", "Superposition (Both!)". "Driving Force Frequency (Motor Speed)" slider. "Wave Mixer" with LEFT and RIGHT "Wave Power" sliders. Status box: Pure State 0, Pure State 1, 50/50 Superposition (Standing Wave), Uneven Mix, or no waves. A displacement graph of all weights | u(x, t) = a_L·A·cos(kx + phase) + a_R·A·cos(kx − phase), with a_L and a_R taken directly from the 0–100% sliders. Wave number k fixed; frequency slider changes only animation speed. Left/right waves have no adjustable relative phase |

### 2.2 Assessment embed: "Superposition Primer Assessment"

Three open-response questions:

1. What is a superposition state?
2. How does a physical phi-bit represented by a spring-mass chain demonstrate
   a superposition state?
3. What are the differences and similarities between a qubit and a coin
   resting on a table?

Each has a text box and a "Copy & Launch Gem" button that copies
"Question: … My Answer: …" to the clipboard and opens the Gem in a new tab.
A footer "Launch Gem" button opens the Gem for free-form questions.

> Note: the site has **three questions for the whole primer**, not a set per
> topic. This spec keeps those three exactly and proposes optional short
> per-topic checks (Section 8.4) for the Spelman team to approve or discard.

---

## 3. Brainstorm

### 3.1 The opportunity: one story across four topics

The four tabs already tell a strong story: *a bit is one state → a coin
analogy → classical waves and modes can combine → a qubit combines states with
probabilities → sound-like waves (phi-bits) can carry qubit-like
superpositions*. Version 2 can make the connective thread visible with
**one shared picture**: every topic's state can be drawn as a point on the
same kind of sphere or as two amplitudes.

| Topic | The two "basis states" | What sets the mix |
|---|---|---|
| Coupled oscillators | Pattern 1 (in step) and Pattern 2 (opposite) | Mode amplitudes A₁, A₂ |
| Qubit | UP \|0⟩ and DOWN \|1⟩ | Amplitudes whose squares are the probabilities, plus a phase |
| Phi-bit | Left-traveling wave (State 0) and right-traveling wave (State 1) | Wave amplitudes a_L, a_R, plus a relative phase |

A small "state card" in the corner of the Topic 2, 3, and 4 pages shows the
current state as two amplitude bars plus a mini Bloch-sphere dot. Students
see that the same mathematics describes all three.

### 3.2 Where the existing app fits

The existing "Superposition vs. mixture" page becomes a **"Go deeper"**
extension of Topic 3 (Electrons & Qubits). It answers a question the coin
analogy raises but cannot settle: *is a superposition just "we don't know
which yet"?* It also adds the phase slider that Topic 3 lacks.

### 3.3 Ideas considered

| Idea | Recommendation |
|---|---|
| Reuse the Spelman canvas animations directly by embedding their HTML | **Not as the main path.** Fastest to reproduce, but Python, the tutor, and the logger can't see slider values inside an embedded page. Possible later as a "classic view" with the team's permission |
| Rebuild visuals in Python with animated Plotly figures | **Recommended.** Physics in Python, so the tutor sees the real numbers and every interaction can be logged. Plotly animations run smoothly in the browser |
| Keep the physics exactly as on the site | **Upgrade it, with defaults that look identical** (Section 6). For example, compute the oscillator patterns from real masses and springs, chosen so the frequencies are still 1.0 and 2.5 |
| Add a relative-phase slider to the phi-bit | **Yes.** It moves the standing wave's still points (nodes), the wave counterpart of φ on the Bloch sphere. At 0 it reproduces the original exactly |
| Show a real Fourier transform on Topic 2 | **Yes.** Compute it from the simulated motion, so the peaks are a measurement rather than a drawing |
| Auto-grade the open-response answers | **Formative feedback only, not grades.** Rubric-based feedback that asks a guiding question and never writes the answer. Scores are stored for research, hidden from students by default |
| Let students revise answers | **Yes.** Each revision is saved, so the learning journey shows how answers change after feedback and after using the simulations |
| Ask for confidence before feedback | **Yes, optional.** A 1–5 rating before feedback is a cheap, useful research measure |
| A "My journey" page for students | **Yes.** Shows their own answers, revisions, and feedback over time and supports reflection |
| Keep the Google Site as the front door | **Possible.** The Streamlit app can be embedded in the Google Site (`?embed=true`) once it runs on an HTTPS campus server. Data still goes only to the campus server |
| Port the Gem's instructions | **Yes, ask the Spelman team for them.** Its instructions and any knowledge files become the tutor's notes, so behavior stays close to what the team designed |

### 3.4 Content notes to discuss with the Spelman team

The Spelman team owns this content. These are suggestions to raise with them,
not changes to make on our own. The tutor's notes will cover these points
whatever wording the pages use, so the chatbot doesn't reinforce a
misconception.

| Where | Current wording or behavior | Why it matters | Suggestion |
|---|---|---|---|
| Topic 3 intro | "hovering in a **mixed state** between the two" | "Mixed state" is the technical term for a classical mixture, the exact opposite idea (and the subject of the "Go deeper" page) | "in a **combination** of the two" |
| Topic 1 | "experiencing a **mix**" | Same ambiguity, milder | "a combination" |
| Topic 1 coin analogy | Spinning coin = superposition | A spinning coin's outcome is set by ordinary physics we just can't track. That makes it closer to a mixture. It has no phase and no interference | Keep the analogy, and add a short "Where the analogy breaks" note linking to "Go deeper" |
| Topic 4 sliders | Labeled "Wave **Power**" but used as **amplitude** | Power grows with amplitude squared. The qubit tab's slider is a probability (also a square) | Label as amplitude and show power and "share of State 1" as readouts, mirroring the qubit's probabilities |
| Topic 4 frequency | Slider changes only animation speed | In a real chain, frequency sets wavelength, and a chain tied to walls has a lowest frequency that can travel | Optional "Go deeper" toggle that uses the chain's real frequency–wavelength relation (Section 6.4) |

---

## 4. What changes in the existing app

### 4.1 From one page to a multipage primer

```
Current                              Version 2
───────                              ─────────
app.py (one page)          ──►       Home
                                     1  Bits & Superposition
                                     2  Coupled Oscillators
                                     3  Electrons & Qubits
                                        └─ Go deeper: Superposition vs. mixture   (existing page)
                                     4  Phi-Bit Systems
                                     5  Test Your Understanding
                                     6  My Journey
                                     (separate app) Instructor Dashboard
```

Every page keeps the existing app's pattern: predict → observe → explain, with
an **"Ask your own questions"** chat panel at the bottom.

### 4.2 Shared sidebar (every page)

1. **Study code and consent** (Section 9.2): a short code entered once per
   session, plus a consent checkbox. Without consent the app works fully and
   nothing is saved.
2. **Progress**: which topics have been visited and which questions answered.
3. **Tutor model**: the existing picker, in `ollama list` order with the top
   model as default. In class mode, the instructor's chosen model is fixed
   and the picker is hidden.

### 4.3 Folder layout

```
superposition_primer/
├── app.py                     # entry point: page navigation, sidebar, session setup
├── README.md
├── requirements.txt
├── config.yaml                # Ollama URL, class/dev mode, tutor model, logging default
├── physics/                   # pure physics; no Streamlit, no language model
│   ├── bits.py
│   ├── oscillators.py
│   ├── qubit.py
│   ├── phibit.py
│   └── mixture.py             # moved from current app.py Part 1 (unchanged)
├── pages/
│   ├── home.py
│   ├── t1_bits.py
│   ├── t2_oscillators.py
│   ├── t3_qubits.py
│   ├── t3b_superposition_vs_mixture.py   # current app.py Parts 2–3, minimal changes
│   ├── t4_phibits.py
│   ├── test_understanding.py
│   └── my_journey.py
├── components/
│   ├── chat_panel.py          # from current app.py Part 4
│   ├── prediction_gate.py     # lock/unlock and re-lock on settings change
│   ├── state_card.py          # amplitudes + mini Bloch sphere (Section 3.1)
│   ├── plots.py               # shared Plotly helpers (springs, masses, spheres)
│   ├── session.py             # study code, consent, progress
│   └── theme.py               # colorblind-safe palette (existing colors kept)
├── tutor.py                   # existing; extended (Section 7)
├── feedback.py                # rubric feedback for Test Your Understanding (Section 8)
├── content/
│   ├── pages.yaml             # page text (Spelman wording, with permission)
│   ├── notes/                 # tutor reference notes per topic (markdown)
│   │   ├── t1_bits.md  t2_oscillators.md  t3_qubits.md  t4_phibits.md
│   ├── questions.yaml         # the three questions + rubrics (Section 8.2)
│   └── quick_checks.yaml      # optional per-topic items (Section 8.4)
├── data/
│   ├── store.py               # all database reads/writes
│   └── schema.sql
├── instructor_app.py          # separate dashboard (Section 10)
└── tests/
```

Code conventions carry over from the existing app: a plain-language docstring
at the top of every file, a docstring on every physics function stating the
formula and units, short functions, and comments that explain *why*.

---

## 5. Page-by-page specification

Each topic page has the same layout:

```
┌───────────────────────────────────────────────────────────────┐
│ Title + one-paragraph intro (Spelman text)                    │
├──────────────────────────────┬────────────────────────────────┤
│ Visual (animated Plotly)     │ Controls, presets              │
│                              │ Predict → Run/Measure → Result │
├──────────────────────────────┴────────────────────────────────┤
│ Explain: secondary plot(s), "Things to try", state card       │
├───────────────────────────────────────────────────────────────┤
│ Ask your own questions (chat)                                 │
├───────────────────────────────────────────────────────────────┤
│ ← Previous topic                               Next topic →   │
└───────────────────────────────────────────────────────────────┘
```

### 5.1 Topic 1 — Bits & Superposition

**Reproduces:** light switch with "Measure Classical Bit"; spinning coin with
"Measure Coin (Slap it down!)" and "Reset (Spin Again)".

**Adds:**
- **Measure 100 coins**: a running tally of heads and tails, so students see
  50/50 emerge (mirrors "Measure 100x" on Topic 3).
- **Predict before measuring**: "If you measure the switch 10 times, how many
  times will it read ON?" and "Out of 100 coin slaps, about how many heads?"
- **"Where the analogy breaks"** expandable note: a spinning coin's result is
  decided by ordinary physics we just can't follow. A real superposition is
  different in a way an experiment can show, with a link to "Go deeper".

**Physics (`physics/bits.py`):**
- `measure_classical(state) -> str` always returns the set state.
- `slap_coins(n, seed, p_heads=0.5) -> (heads, tails)`.

**Logged events:** toggle, measure (classical/coin), prediction, 100-coin run.

### 5.2 Topic 2 — Coupled Oscillators

**Reproduces:** two weights between walls; initial-position sliders
(−80 to 80, default 40 and 40); presets "Pattern 1 Only (Both Right)" (40, 40),
"Pattern 2 Only (Opposite)" (40, −40), "Random Superposition (Mix!)"
(random with |x₁| ≠ |x₂|); weight 1 position over time; pattern bar chart.

**Physics upgrade (`physics/oscillators.py`):**
- System: wall – spring k – mass m – coupling spring k_c – mass m – spring
  k – wall.
- `normal_modes(k, k_c, m) -> (frequencies, mode_vectors)` from the
  eigenvalues of the 2×2 stiffness matrix. Default k = m = 1, k_c = 2.625
  gives ω₁ = 1.0 and ω₂ = 2.5, matching the original exactly. Mode vectors
  are (1, 1)/√2 and (1, −1)/√2.
- `mode_amplitudes(x1_0, x2_0) -> (A1, A2)`, with A₁ = (x₁ + x₂)/2 and
  A₂ = (x₁ − x₂)/2 (released from rest, as in the original).
- `positions(t, x1_0, x2_0, k, k_c, m) -> (x1, x2)`.
- `spectrum(trace, dt) -> (omega, amplitude)` by FFT of the simulated motion.

**Adds:**
- The bar chart becomes a real frequency spectrum computed from the motion,
  with peaks labeled Pattern 1 and Pattern 2.
- Optional "Go deeper" slider for coupling strength k_c, so students see
  Pattern 2's frequency move while Pattern 1's stays fixed.
- Prediction: "With weight 1 at Right 40 and weight 2 at center, which
  patterns will light up?" (both, equal amounts).
- State card: A₁ and A₂ as two amplitude bars and a point on the sphere,
  so students see that this is a two-component state, like a qubit.

**Animation:** Plotly frames for one long loop (about 12 s), with play and
pause. The springs are drawn as zigzag lines and the weights as circles.
Time step and trace length match the original look (about 200 points).

**Logged events:** slider set (final value, not every drag tick), preset,
prediction, play/pause.

### 5.3 Topic 3 — Electrons & Qubits

**Reproduces:** Bloch-sphere arrow; probability slider from 100% DOWN to 100%
UP (default 50/50); "Measure 1x" (arrow snaps to UP or DOWN); "Measure 100x"
(adds 100 results and resets the arrow); results bars with counts;
"Clear Data".

**Physics (`physics/qubit.py`, reusing `physics/mixture.py`):**
- `theta_from_probability(p_up) -> theta_deg` = 2·arccos(√p_up).
- `measure(p_up, n, seed) -> (ups, downs)`.

**Adds:**
- Prediction before "Measure 100x": "About how many UP results out of 100?"
  The app then shows the actual count and how far off it was.
- A "sample size" note with a small chart showing how the measured fraction
  settles toward the set probability as counts grow.
- **"Go deeper: Superposition vs. mixture"**, the existing page, which adds the
  phase φ and the comparison with a classical mixture.

**Logged events:** slider set, measure 1x, measure 100x, clear, prediction,
"Go deeper" opened.

### 5.4 Topic 3b — Go deeper: Superposition vs. mixture

The existing app's Parts 2 and 3, moved into a page, with three changes:

1. Use the shared `prediction_gate` so changing any setting after a run
   **re-locks the experiment** until a new prediction is made. This fixes the
   current behavior, where results update without a new prediction.
2. Use the shared chat panel and logger.
3. Add a short intro linking back to the Topic 1 coin and the Topic 3
   slider.

### 5.5 Topic 4 — Phi-Bit Systems

**Reproduces:** chain of 12 weights with side springs and a driver; presets
"State 0 (100% Left)", "State 1 (100% Right)", "Superposition (Both!)";
driving-frequency slider (Slow–Fast, default 1.5); LEFT and RIGHT sliders;
status box (Pure State 0, Pure State 1, 50/50 Superposition (Standing Wave),
Uneven Mix, or no waves); displacement graph with colored dots under each
weight.

**Physics (`physics/phibit.py`):**
- `displacement(x, t, a_left, a_right, delta_deg, k, omega)`
  = a_L·cos(kx + ωt) + a_R·cos(kx − ωt + δ).
  With δ = 0 this is the original formula.
- `classify(a_left, a_right) -> str` with the same five categories and the
  same wording as the original status box.
- `bloch_from_amplitudes(a_left, a_right, delta_deg) -> (theta_deg, phi_deg)`
  with θ = 2·arctan(a_R/a_L) and φ = δ. "Share of State 1" =
  a_R²/(a_L² + a_R²), which is exactly the qubit's probability formula.
- `node_positions(k, delta_deg, length)`: for a_L = a_R the wave is
  2a·cos(kx + δ/2)·cos(ωt − δ/2), so the still points sit where
  cos(kx + δ/2) = 0, shifted by δ/(2k) as δ changes.

**Adds:**
- **Relative phase slider δ** (0–359°, default 0) in the Wave Mixer, with a
  prediction: "If you change the phase while the mix is 50/50, what happens
  to the still points?" (They slide along the chain; the wave stays
  standing.)
- **Amplitude labels and readouts** (Section 3.4): sliders labeled
  amplitude, with readouts for power and share of State 1.
- **State card** with the mini Bloch sphere, showing the phi-bit state
  traced on the same sphere as the qubit.
- **"Same and different" panel**: like a qubit, the phi-bit's state is a
  combination of two basis states with amplitudes and a phase. Unlike a
  qubit, both waves can be observed at once without the state snapping to
  one of them. This supports Question 3 and the NewFoS idea of classical
  analogs of qubits.
- **Optional "Go deeper"** (Section 6.4): use the chain's real
  frequency–wavelength relation, so the driving frequency sets the
  wavelength and frequencies below the chain's lowest allowed frequency give
  no traveling wave.

**Logged events:** preset, sliders (final values), phase set, prediction,
"Go deeper" toggled.

### 5.6 Test Your Understanding

See Section 8.

### 5.7 My Journey (student view)

A timeline of the student's own activity in this and earlier sessions with
the same study code: topics visited, predictions and whether they matched,
each answer with its revisions and the feedback received, and their chat
questions. Students can download it as a PDF or Markdown summary.

---

## 6. Physics checks (tests that must pass)

### 6.1 Topic 1
- `measure_classical` returns the set state 100% of the time.
- `slap_coins(10000)` gives heads within 4 standard errors of 5,000 for
  99.9% of 1,000 seeds.

### 6.2 Topic 2
- Default parameters give ω₁ = 1.000 and ω₂ = 2.500 (to 1e-9) and mode
  vectors (1, 1)/√2 and (1, −1)/√2.
- The closed-form motion matches a direct numerical solution of Newton's
  equations to 1e-6 (verified while writing this spec: about 2e-8 over 30
  time units).
- The FFT of x₁(t) has peaks at ω₁ and ω₂ with heights |A₁| and |A₂|
  (verified for x₁ = 40, x₂ = −10: peaks of 15 and 25).
- Pattern 1 preset → A₂ = 0; Pattern 2 preset → A₁ = 0.

### 6.3 Topic 3
- θ = 90° at 50%, 0° at 100% UP, 180° at 100% DOWN.
- Measured UP fraction over 10,000 shots within 4 standard errors of p_up.
- The existing Superposition vs. mixture tests continue to pass.

### 6.4 Topic 4
- δ = 0 reproduces the original displacement formula exactly.
- a_L = a_R: the displacement factors into a fixed shape times a time
  oscillation (standing wave); nodes do not move in time; nodes shift by
  δ/(2k) as δ changes.
- `bloch_from_amplitudes(0.8, 0.6, 0)` gives θ ≈ 73.74° and share of
  State 1 = 0.36.
- `classify` returns the original five labels for the original preset values.
- Optional chain physics (Go deeper): for a chain of masses m, neighbor
  springs K, and side springs k₀, ω² = k₀/m + (4K/m)·sin²(qa/2). The
  numerical normal modes of a 12-mass chain fall within that band.

---

## 7. The chatbot: "Ask your own questions"

### 7.1 Where it appears

- At the bottom of **every topic page**, aware of that page and its current
  settings.
- On **Test Your Understanding**, a "Discuss this question" button under each
  question opens the chat with the question and the student's latest answer
  already included. This replaces the Gem's copy-and-paste step.
- A general chat on the Home page for questions about the whole primer
  (replaces the footer "Launch Gem" button).

### 7.2 What the tutor receives

Built by `tutor.build_system_prompt(page, context)`, extended from the
existing function:

1. Role and rules: the existing tutor rules (short answers, plain language,
   guiding question first when the student seems to be guessing, LaTeX math,
   never invent numbers).
2. The page's reference notes from `content/notes/` (Spelman content plus
   the accuracy notes in Section 3.4). This is also where the Gem's
   instructions go once the Spelman team shares them.
3. The page's live context: current slider values, presets, measurement
   counts, and predictions, from the page's `tutor_context()` function.
   Results are included only after the student has run or measured.
4. Recent conversation (last 10 messages, as now).

### 7.3 Behavior rules

| Situation | Tutor behavior |
|---|---|
| Before a prediction is made | Helps the student reason; doesn't reveal the outcome |
| Test Your Understanding discussion | Asks guiding questions and points to a simulation to revisit; **does not write or rewrite the answer**, even if asked |
| Coin-analogy questions | Explains the analogy's value and its limit (Section 3.4) |
| Off-topic | One sentence, then steers back |
| Unsure or unsupported | Says so; offers to flag the question for the instructor |

Existing features are kept: model list in `ollama list` order with the top
model as default, streaming answers, hiding `<think>` text from reasoning
models, and clear messages when Ollama is off or an embedding model is chosen.

---

## 8. Test Your Understanding (in-app)

### 8.1 Student flow

```
Read question ─► Write answer ─► (optional) Rate confidence 1–5 ─► Submit
      ▲                                                               │
      │                                                               ▼
  Revise answer ◄── Read feedback (strength + guiding question + "revisit" link)
      │
      └──► "Discuss this question" (chat, seeded with question + latest answer)
```

- Every submission is saved as a numbered attempt. Earlier attempts are never
  overwritten.
- Feedback comes after each submission (instructor can turn it off for a
  pre-test).
- A "revisit" link opens the relevant topic page with a preset that targets
  the gap (for example, Topic 4 with the 50/50 preset).
- Students can move between questions freely; drafts are kept while they do.

### 8.2 Questions and draft rubrics (`content/questions.yaml`)

The question wording is the Spelman team's, kept exactly. The key ideas below
are **drafts for the Spelman team to edit and approve** before use.

**Q1. What is a superposition state?**
- Key ideas:
  - k1: a combination of two (or more) basic states at once;
  - k2: each part has a weight (amplitude) that sets how likely each
    measurement result is;
  - k3: measuring gives just one of the basic states;
  - k4 (advanced): it is not the same as "secretly one or the other";
    the relative phase matters.
- Misconceptions to detect: "it is secretly one state and we just don't
  know" (M-mixture); "it is both in the everyday sense, like two objects"
  (M-classical-both).
- Revisit links: Topic 3 slider; Go deeper page.

**Q2. How does a physical phi-bit represented by a spring-mass chain
demonstrate a superposition state?**
- Key ideas:
  - k1: the chain supports two basic states, a left-traveling wave (State 0)
    and a right-traveling wave (State 1);
  - k2: both can be present at once with adjustable amounts;
  - k3: an equal mix forms a standing wave, an uneven mix a "lumpy"
    traveling wave;
  - k4: this parallels a qubit's two basis states and their amplitudes;
  - k5 (advanced): unlike a qubit, both waves can be observed at once
    without the state snapping to one of them.
- Misconceptions to detect: "superposition only happens to tiny quantum
  objects"; confusing the standing wave with the absence of waves.
- Revisit links: Topic 4 presets; phase slider.

**Q3. What are the differences and similarities between a qubit and a coin
resting on a table?**
- Key ideas:
  - k1 (similarity): both have two possible results (heads/tails, UP/DOWN),
    and looking gives one of them;
  - k2 (difference): a resting coin is already in one definite state; it is
    a classical bit, not a superposition;
  - k3 (difference): a qubit can be in a combination with amplitudes (and a
    phase), so its results are probabilistic;
  - k4 (advanced): measuring a qubit changes its state; looking at a coin
    doesn't. Qubit superpositions can interfere; coins can't.
- Misconceptions to detect: "a resting coin is in superposition until you
  look"; "a qubit is just like a spinning coin".
- Revisit links: Topic 1; Topic 3; Go deeper page.

### 8.3 How feedback is produced (`feedback.py`)

Two steps, both run on the local model, with checks in code between them.

1. **Rubric check (structured output).** The model returns JSON in a fixed
   format (Ollama's `format` option with a JSON schema):

   ```json
   {
     "question_id": "q3",
     "key_ideas": [
       {"id": "q3.k1", "status": "present", "evidence": "both have two sides"},
       {"id": "q3.k2", "status": "absent",  "evidence": ""}
     ],
     "misconceptions": [
       {"id": "M-coin-superposition", "evidence": "the coin is both until you look"}
     ],
     "level": "developing"
   }
   ```

   **Checks in code** (constraint-first):
   - every `evidence` string must appear in the student's answer (word for
     word, ignoring case and spacing); otherwise the idea is set to
     "absent" and the check is re-run once;
   - only IDs defined in `questions.yaml` are accepted;
   - `level` must be one of beginning / developing / proficient.

2. **Feedback text.** A second call writes 3–5 sentences for the student
   from the checked JSON:
   - one specific strength, quoting their words;
   - one gap, phrased as a guiding question (never the answer);
   - a revisit link to a simulation preset;
   - no score or level shown to students (instructor setting).

A code check rejects feedback that contains rubric wording copied as a model
answer (overlap with the key-idea text above a threshold) and retries once.
If it fails again, the student sees a short neutral message and a revisit
link, and the attempt is flagged for instructor review.

### 8.4 Optional per-topic quick checks (`content/quick_checks.yaml`)

Two short multiple-choice items per topic give clear, comparable data on top
of the open answers. These are **draft items for the Spelman team**, shown
at the end of each topic page as "Quick check".

| Topic | Item | Answer |
|---|---|---|
| 1 | A coin resting heads-up on a table is best described as: (a) a superposition of heads and tails (b) a classical bit in a definite state (c) 50% heads (d) undefined until someone looks | b |
| 1 | You slap 100 spinning coins. The most reasonable expectation is: (a) exactly 50 heads (b) close to 50 heads, but rarely exactly 50 (c) all heads or all tails (d) impossible to say | b |
| 2 | Both weights start at Right 40. Which patterns play? (a) Pattern 1 only (b) Pattern 2 only (c) both (d) neither | a |
| 2 | Weight 1 at Right 40, weight 2 at center. Which patterns play? (a) Pattern 1 only (b) Pattern 2 only (c) both, equally (d) neither | c |
| 3 | You set 70% UP and measure 100 times. Most likely: (a) exactly 70 UP (b) about 70 UP (c) 50 UP (d) 100 UP | b |
| 3 | A measurement just gave UP. You measure again right away. You get: (a) UP (b) DOWN (c) 70% chance UP (d) 50/50 | a |
| 4 | Left and right amplitudes are equal. The chain shows: (a) no wave (b) a standing wave (c) a left-traveling wave (d) a right-traveling wave | b |
| 4 | Only the right wave is on. This is: (a) State 0 (b) State 1 (c) a 50/50 superposition (d) a standing wave | b |

Each item has feedback for every wrong option and a revisit link, as in the
item format of the series spec.

---

## 9. Learning-journey data

### 9.1 Principles

- **Nothing leaves the machine or campus server.** No external AI service is
  used.
- **Logging only with consent** and an approved IRB protocol. Without
  consent, the app works fully and saves nothing.
- **No names.** Students enter a study code issued by the instructor (or a
  code they choose, if the protocol allows). The code is stored only as a
  keyed hash. The key is held by the PI and stored separately from the data.
- Returning with the same code restores the student's answers and journey.

### 9.2 Session start

1. Student opens the app.
2. Sidebar asks for the study code and shows the consent text approved by
   the IRB, with "I agree" and "Continue without saving" choices.
3. Class mode only: the instructor's course code selects the section and its
   settings (feedback on/off, quick checks on/off).

### 9.3 Database (`data/schema.sql`, SQLite in WAL mode)

| Table | Fields |
|---|---|
| `students` | student_key (hashed code), section, consent_version, created_at |
| `sessions` | session_id, student_key, started_at, ended_at, app_version, mode |
| `events` | session_id, ts, page, event_type, details (JSON: slider values, preset name, counts) |
| `predictions` | session_id, ts, page, question, prediction, correct_answer, matched |
| `tyu_attempts` | attempt_id, session_id, ts, question_id, attempt_no, answer, confidence, rubric_json, feedback_text, model, model_digest, flagged |
| `quick_check_responses` | session_id, ts, item_id, choice, correct |
| `chat_turns` | session_id, ts, page, seeded_from (null or question_id), question, answer, model, model_digest, context_json, latency_ms |
| `ratings` | chat_turn_id or attempt_id, helpful (yes/no), comment |

Event types: `page_view`, `page_leave` (with time on page), `slider_set`,
`preset`, `measure`, `play`, `pause`, `go_deeper_open`, `prediction`,
`quick_check`, `tyu_submit`, `tyu_feedback_view`, `revisit_link`,
`chat_open`, `chat_turn`.

Slider events record final values (after a short pause), not every drag
step, to keep the log readable.

### 9.4 What the data can show

| Question about learning | Evidence |
|---|---|
| Do answers improve after feedback? | Rubric key ideas per attempt, attempt 1 vs. final |
| Which simulations help? | Revisit-link use and simulation events between attempts, followed by key-idea changes |
| Which misconceptions persist? | Misconception flags across attempts and quick checks |
| Is confidence calibrated? | Confidence ratings vs. rubric results |
| What do students ask on their own? | Chat questions coded by topic and type |
| How do students move through the primer? | Page order, time on page, revisits |

---

## 10. Instructor dashboard (`instructor_app.py`)

A separate Streamlit app, available only to instructors (password from an
environment variable on a laptop; campus sign-in on a server).

| View | Contents |
|---|---|
| Overview | Number of students, completion by topic, median time per topic |
| Questions | For each question: key-idea coverage on first vs. final attempt; misconception counts; anonymized sample answers |
| Feedback review | Flagged attempts and a random sample each week to rate the feedback (appropriate / partly / wrong). Disagreements are stored |
| Chat | Questions by page; most common themes; turns marked "not helpful" |
| Quick checks | Percent correct per item; most chosen wrong options |
| Journey | One anonymized student's timeline (by hashed code) |
| Settings | Feedback on/off, quick checks on/off, tutor model, consent text version |
| Export | De-identified CSV files of every table, plus a data dictionary |

---

## 11. Deployment options

| Option | Use | Notes |
|---|---|---|
| Laptop | Development, demos, small pilot | `streamlit run app.py` with Ollama on the same laptop (as now) |
| Campus server | Class use | Ollama and the app on the campus GPU server; HTTPS reverse proxy; nightly database backup |
| Inside the Google Site | Keep the Spelman site as the front door | Embed the server's app URL with `?embed=true`. Requires the campus server and HTTPS; data still stays on campus |

Rough capacity targets for a class of 30: simulation response under 1 s;
first tutor text under 3 s; feedback under 15 s. Confirm with a load test
before the first class.

---

## 12. Testing

| Area | Tests |
|---|---|
| Physics | All checks in Section 6 as automated tests |
| Pages | Streamlit `AppTest` for each page: controls work, predictions lock and unlock, settings changes re-lock, page works with Ollama off |
| Chat | Stand-in Ollama server (as used for the current app): model list order and default, streaming, `<think>` filtering, page context included, results withheld before measuring |
| Test Your Understanding | Submit → attempt saved → rubric JSON checked → feedback shown; evidence check rejects invented quotes; feedback never contains a model answer; attempts never overwritten |
| Data | No rows written without consent; same study code restores the journey; deletion script removes all rows for a code; export contains no raw codes |
| Feedback quality | 20–30 sample answers per question, written to cover each key idea and misconception, scored by a physicist. Target: the rubric check agrees with the physicist on at least 85% of key-idea decisions before student use |
| Accessibility | Keyboard use, text summaries of every animation, colorblind-safe palette, pause control for every animation |

---

## 13. Build plan

| Step | Work | Rough effort (one developer) |
|---|---|---|
| 1 | Restructure into pages; move current app into Topic 3b; shared sidebar, prediction gate, chat panel | 2–3 days |
| 2 | Topics 1, 2, 3, and 4 pages with physics, animations, and tests | 6–8 days |
| 3 | Test Your Understanding with saved attempts and rubric feedback | 4–5 days |
| 4 | Study code, consent, logging, and My Journey page | 3–4 days |
| 5 | Instructor dashboard and export | 3–4 days |
| 6 | Feedback-quality check, accessibility pass, load test, README | 3–4 days |

Total: about 4–6 weeks of focused work. Steps 1–2 alone give a working
four-topic primer with the local chatbot; steps 3–5 add the research data.

---

## 14. Before building: items for the Spelman team

1. **Permission and credit**: confirm we may reproduce the primer's text,
   structure, and questions, and agree on how the team is credited in the
   app (for example, an "About" page and footer).
2. **The Gem's setup**: its instructions and any knowledge files, so the
   local tutor can follow the same approach.
3. **Rubrics**: edit and approve the draft key ideas (Section 8.2).
4. **Quick checks**: keep, edit, or drop (Section 8.4).
5. **Content notes**: review the wording suggestions (Section 3.4).
6. **Research setup**: IRB protocol, consent text, and how study codes are
   issued.
7. **Hosting**: laptop pilot first, or campus server and Google Site embed.

---

## 15. How this fits the proposal

- Builds on **Spelman faculty work**: the primer and its questions come from
  the Spelman team. The proposal's infrastructure (local models, logging,
  faculty-controlled tutors) is what turns it into a research instrument.
- Fixes a concrete problem with off-the-shelf tools: a Gem can't give
  faculty the data needed to study learning. Locally hosted agents can.
- Gives a small, realistic pilot whose data (answer revisions, feedback
  effects, student questions) can serve as preliminary evidence for the
  research questions on platform effectiveness and student learning.
