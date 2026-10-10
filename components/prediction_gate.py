"""
components/prediction_gate.py — predict first, then observe
===========================================================

Every simulation in the primer follows predict -> observe -> explain. This
gate enforces the first step: the "run" button stays locked until the
student has made a prediction.

It also RE-LOCKS. If the student changes a setting after running, the old
result no longer belongs to what is on screen, so the result is hidden and
the prediction is cleared until they predict again. Without this, students
could sweep a slider and watch results update without ever predicting.

HOW A PAGE USES IT
------------------
    gate = prediction_gate("t3b", signature=(theta, phi, axis))
    gate.ask_choice("The two states will give...", ["the same", "different"])
    if gate.run_button("Run the experiment"):
        ...show results...

`signature` is a tuple of every setting the result depends on.
"""

import streamlit as st

NO_CHOICE = "Choose one"


class PredictionGate:
    """Holds one prediction and whether the experiment has been run for it."""

    def __init__(self, key: str, signature: tuple):
        self.key = key
        self.signature = signature
        self.prediction = None      # the student's prediction, or None
        state = st.session_state
        # True only on the redraw right after the run button was clicked.
        self.just_ran = state.pop(f"{key}_just_ran", False)

        # Settings changed since the last run: hide the result and clear the
        # prediction. This must happen before the prediction widget is drawn.
        ran_for = state.get(f"{key}_ran_for")
        if ran_for is not None and ran_for != signature:
            state[f"{key}_ran_for"] = None
            state[f"{key}_relocked"] = True
            state.pop(f"{key}_prediction", None)

    @property
    def ran(self) -> bool:
        """True after Run, until a setting in the signature changes."""
        return st.session_state.get(f"{self.key}_ran_for") == self.signature

    def _relock_notice(self):
        if st.session_state.get(f"{self.key}_relocked"):
            st.info("Settings changed. Make a new prediction to run again.")

    def ask_choice(self, question: str, options: list[str]):
        """Ask a multiple-choice prediction. Returns the choice, or None."""
        self._relock_notice()
        _keep(f"{self.key}_prediction", NO_CHOICE)
        # Once the result is showing, the prediction is fixed: otherwise it
        # could be edited afterwards to "match".
        choice = st.radio(question, [NO_CHOICE] + list(options),
                          key=f"{self.key}_prediction", disabled=self.ran)
        self.prediction = None if choice == NO_CHOICE else choice
        return self.prediction

    def ask_number(self, question: str, low: int, high: int):
        """Ask for a whole-number prediction. Returns the number, or None."""
        self._relock_notice()
        _keep(f"{self.key}_prediction", None)
        self.prediction = st.number_input(
            question, min_value=low, max_value=high, step=1,
            placeholder="Type a number", key=f"{self.key}_prediction",
            disabled=self.ran)
        return self.prediction

    def run_button(self, label: str) -> bool:
        """
        Draw the run button (locked until there is a prediction).
        Returns True while the result for the current settings should show.
        """
        if self.prediction is None:
            st.info("Make a prediction to unlock the experiment.")
            return False
        st.button(label, type="primary", key=f"{self.key}_run",
                  on_click=self._mark_run)
        return self.ran

    def new_prediction_button(self, label: str = "Make a new prediction") -> None:
        """
        Draw a button that unlocks the prediction again. For experiments
        with no setting to change, where nothing else would unlock it.
        Shown only while a result is on screen.
        """
        if self.ran:
            st.button(label, key=f"{self.key}_again", on_click=reset_gate,
                      args=(self.key,))

    def _mark_run(self) -> None:
        """
        Runs when the button is clicked, BEFORE the page is redrawn, so the
        prediction is already locked when it is drawn next to the result.
        """
        st.session_state[f"{self.key}_ran_for"] = self.signature
        st.session_state[f"{self.key}_relocked"] = False
        st.session_state[f"{self.key}_just_ran"] = True


def _keep(key: str, default) -> None:
    """Keep a widget's value across visits to other pages (see layout.keep)."""
    st.session_state[key] = st.session_state.get(key, default)


def reset_gate(key: str) -> None:
    """Forget the run and the prediction (for a page's "clear" button)."""
    st.session_state[f"{key}_ran_for"] = None
    st.session_state[f"{key}_relocked"] = False
    st.session_state.pop(f"{key}_prediction", None)


def prediction_gate(key: str, signature: tuple) -> PredictionGate:
    """Create the gate for one experiment. `key` must be unique on the page."""
    return PredictionGate(key, signature)
