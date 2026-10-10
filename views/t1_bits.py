"""
views/t1_bits.py — Topic 1: Bits & Superposition
================================================

WHAT THIS PAGE TEACHES
----------------------
A classical bit (a light switch) is always in one definite state: measure
it as often as you like and you get the same answer. A spinning coin is a
first picture of a superposition: you can't say heads or tails until you
slap it down, and then you get exactly one of them, about half the time
each.

The page also says where the coin picture stops being true, and points to
the "Go deeper" page for the experiment that shows the difference.

The rules are in physics/bits.py.
"""

import random

import streamlit as st

from components import journey, layout, plots
from components.chat_panel import chat_panel
from components.coin import coin as draw_coin
from components.light_switch import light_switch
from components.prediction_gate import prediction_gate, reset_gate
from components.quick_check import quick_check
from physics import bits

PAGE_ID = "t1"
state = st.session_state

# Each visit gets its own random starting point; every measurement after
# that uses a new seed, so results differ from click to click.
state.setdefault("t1_seed", random.randrange(1_000_000))
state.setdefault("t1_draws", 0)
state.setdefault("t1_coin", None)        # None = still spinning
state.setdefault("t1_tally", [0, 0])     # [heads, tails] over all 100-coin runs


def next_seed() -> int:
    """A new seed for each measurement."""
    state["t1_draws"] += 1
    return state["t1_seed"] + state["t1_draws"]


text = layout.page_header(PAGE_ID)
bit_side, coin_side = st.columns(2)

# ---------------- The classical bit ----------------
with bit_side:
    st.subheader(text["classical_heading"])
    st.markdown(text["classical_text"])

    layout.keep("t1_switch_on", True)
    switch_on = st.toggle("Flip the switch to toggle:", key="t1_switch_on")
    switch = "ON" if switch_on else "OFF"
    # Animate only on the run where the switch changed, so it does not
    # move by itself when the page opens or another control is used.
    flipped = state.get("t1_switch_drawn", switch_on) != switch_on
    state["t1_switch_drawn"] = switch_on
    light_switch(switch_on, flipped)
    st.markdown(f"The switch is **{switch}**.")

    if st.button("Measure Classical Bit", key="t1_measure_bit"):
        result = bits.measure_classical(switch)
        st.success(f"Measurement Result: It is exactly {result}.")
        journey.record("measure_bit", PAGE_ID, switch=switch, result=result)

    st.markdown("**Predict**")
    bit_gate = prediction_gate("t1_switch10", (switch,))
    bit_gate.ask_number(
        "If you measure the switch 10 times, how many times will it read ON?",
        0, 10)
    times_on = None
    if bit_gate.run_button("Measure the switch 10 times"):
        times_on = sum(bits.measure_classical(switch) == "ON" for _ in range(10))
        st.markdown(f"The switch read **ON {times_on} times out of 10**.")
        matched = bit_gate.prediction == times_on
        if matched:
            st.success("Your prediction matches. A classical bit is in one "
                       "definite state, so every measurement agrees.")
        else:
            st.warning(f"You predicted {bit_gate.prediction}. Why does a "
                       f"switch give the same reading every time?")
        if bit_gate.just_ran:
            journey.record("measure_bit_10", PAGE_ID, switch=switch,
                           prediction=bit_gate.prediction, times_on=times_on,
                           matched=matched)
        st.caption("Your prediction is locked while this result is showing.")
        bit_gate.new_prediction_button()

# ---------------- The spinning coin ----------------
with coin_side:
    st.subheader(text["superposition_heading"])
    st.markdown(text["superposition_text"])

    def press_coin():
        """Slap the coin down, or set it spinning again."""
        if state["t1_coin"] is None:
            heads, _ = bits.slap_coins(1, next_seed())
            state["t1_coin"] = "HEADS" if heads else "TAILS"
            journey.record("measure_coin", PAGE_ID, result=state["t1_coin"])
        else:
            state["t1_coin"] = None

    coin = state["t1_coin"]
    layout.keep("t1_pause", False)
    paused = st.toggle("Pause the coin", key="t1_pause",
                       help="Stops the spinning animation.")
    draw_coin(coin, paused)
    if coin is None:
        st.markdown("The coin is spinning in a blur of both Heads and Tails!")
        if paused:
            st.caption("Animation paused. The coin is still unmeasured: it "
                       "shows \"?\" because neither face has been picked.")
    else:
        st.markdown(f"The superposition collapsed! "
                    f"**You looked! It snapped to: {coin}**")
    st.button("Measure Coin (Slap it down!)" if coin is None
              else "Reset (Spin Again)", key="t1_coin_btn", on_click=press_coin)

    st.markdown("**Predict**")
    coin_gate = prediction_gate("t1_coin100", ())
    coin_gate.ask_number("Out of 100 coin slaps, about how many heads?", 0, 100)
    if coin_gate.run_button("Measure 100 coins"):
        if coin_gate.just_ran:
            heads, tails = bits.slap_coins(100, next_seed())
            state["t1_tally"] = [state["t1_tally"][0] + heads,
                                 state["t1_tally"][1] + tails]
            state["t1_last100"] = heads
            journey.record("measure_100_coins", PAGE_ID,
                           prediction=coin_gate.prediction, heads=heads,
                           off_by=abs(heads - coin_gate.prediction))
        heads = state["t1_last100"]
        st.markdown(
            f"This run: **{heads} heads** and {100 - heads} tails. You "
            f"predicted {coin_gate.prediction}, so you were off by "
            f"{abs(heads - coin_gate.prediction)}. Press the button again: "
            f"do you get the same number?")
        st.caption("Your prediction is locked while this result is showing.")
        # The coin has no setting to change, so nothing else would unlock it.
        coin_gate.new_prediction_button()

# ---------------- Explain ----------------
st.divider()
st.subheader("Explain")
tally_side, notes_side = st.columns(2)
heads_total, tails_total = state["t1_tally"]

with tally_side:
    st.markdown("**Running tally of every 100-coin run**")
    st.plotly_chart(plots.count_bars(["HEADS", "TAILS"],
                                     [heads_total, tails_total]),
                    width="stretch")
    total = heads_total + tails_total
    if total:
        st.caption(f"Chart: {heads_total} heads and {tails_total} tails out "
                   f"of {total} coins ({heads_total / total:.1%} heads). The "
                   f"more coins, the closer the fraction settles to 50%, even "
                   f"though no single slap can be predicted.")
        if st.button("Clear tally", key="t1_clear",
                     help="Also unlocks the prediction, so you can make a "
                          "new one."):
            state["t1_tally"] = [0, 0]
            reset_gate("t1_coin100")
            st.rerun()
    else:
        st.caption("Chart: empty until you measure 100 coins.")

with notes_side:
    layout.things_to_try(text)
    with st.expander("Where the analogy breaks"):
        st.markdown(text["analogy_breaks"])
        if st.button("Open Go deeper: Superposition vs. mixture",
                     key="t1_go_deeper"):
            journey.record("go_deeper_open", PAGE_ID)
            layout.go_to("t3b")


# ---------------- Ask your own questions ----------------
def tutor_context() -> dict:
    """What the tutor is told about this page right now."""
    measured = total > 0
    return {
        "page_id": PAGE_ID,
        "page_title": text["title"],
        "controls": "the light switch and its Measure button, the coin's "
                    "Measure/Reset button, the two predictions, the 100-coin "
                    "tally chart",
        "settings_lines": [
            f"Light switch is {switch}",
            "Coin is still spinning" if coin is None
            else f"Coin was slapped down and shows {coin}",
            f"Prediction for ON readings out of 10: "
            f"{bit_gate.prediction if bit_gate.prediction is not None else 'none yet'}",
            f"Prediction for heads out of 100: "
            f"{coin_gate.prediction if coin_gate.prediction is not None else 'none yet'}",
        ],
        "results_lines": [
            f"100-coin tally so far: {heads_total} heads, {tails_total} "
            f"tails out of {total} coins",
        ] if measured else [],
        "revealed": measured,
        "hold_back": "how many heads to expect out of 100, or how many ON "
                     "readings out of 10",
    }


quick_check(PAGE_ID)
chat_panel(tutor_context(), starter_questions=text["starter_questions"])
layout.prev_next(PAGE_ID)
