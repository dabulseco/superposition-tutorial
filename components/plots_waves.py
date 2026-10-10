"""
components/plots_waves.py — drawings of weights, springs, and waves
===================================================================

The animated pictures for Topic 2 (two weights on springs) and Topic 4 (a
chain of twelve weights), plus their line charts. No physics is done here:
positions come from physics/oscillators.py and physics/phibit.py.

HOW THE ANIMATIONS WORK
-----------------------
Plotly animations are a list of "frames". We calculate the picture at each
moment in Python, hand all the frames to the browser at once, and the
browser plays them. That keeps playback smooth, and the Play and Pause
buttons work without the page reloading.
"""

import numpy as np
import plotly.graph_objects as go

from components.plots import spring_points
from components.theme import (COLOR_NEUTRAL, COLOR_PURE, COLOR_STATE0,
                              COLOR_STATE1)

FRAME_MS = 80        # time each frame is shown, in milliseconds


def _play_pause(frame_ms: int = FRAME_MS) -> list[dict]:
    """Play and Pause buttons for an animated figure."""
    return [dict(
        type="buttons", direction="left", x=0.0, y=1.18, xanchor="left",
        showactive=False,
        buttons=[
            dict(label="▶ Play", method="animate",
                 args=[None, dict(frame=dict(duration=frame_ms, redraw=False),
                                  transition=dict(duration=0),
                                  fromcurrent=True, mode="immediate")]),
            dict(label="⏸ Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False),
                                    mode="immediate")]),
        ])]


# -----------------------------------------------------------------------------
# Topic 2: two weights between walls
# -----------------------------------------------------------------------------

WALL_X = 3.0                 # walls at -3 and +3 (drawing units)
REST_X = (-1.0, 1.0)         # where the weights sit at rest
PULL_SCALE = 0.8 / 80        # a slider value of 80 moves a weight 0.8 units


def _oscillator_shapes(x1, x2):
    """Spring and weight coordinates for one moment."""
    p1 = REST_X[0] + x1 * PULL_SCALE
    p2 = REST_X[1] + x2 * PULL_SCALE
    xs, ys = [], []
    for start, end in [(-WALL_X, p1 - 0.18), (p1 + 0.18, p2 - 0.18),
                       (p2 + 0.18, WALL_X)]:
        sx, sy = spring_points(start, end, 0, coils=7, half_width=0.12)
        xs += list(sx) + [None]      # None lifts the pen between springs
        ys += list(sy) + [None]
    return xs, ys, [p1, p2]


def oscillator_animation(times, x1, x2) -> go.Figure:
    """Two weights joined by zigzag springs, animated over `times`."""
    def traces(i):
        xs, ys, masses = _oscillator_shapes(x1[i], x2[i])
        return [
            go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="skip",
                       line=dict(color=COLOR_NEUTRAL, width=2)),
            go.Scatter(x=masses, y=[0, 0], mode="markers+text",
                       text=["1", "2"], textfont=dict(color="white", size=14),
                       hoverinfo="skip",
                       marker=dict(size=38, color=[COLOR_PURE, COLOR_STATE1])),
        ]

    names = [str(i) for i in range(len(times))]
    fig = go.Figure(
        data=traces(0),
        frames=[go.Frame(data=traces(i), name=names[i])
                for i in range(len(times))])
    # Play runs through the list of frame names; repeating the names
    # replays the motion without sending the frames to the browser again.
    menu = _play_pause()
    menu[0]["buttons"][0]["args"][0] = names * 5
    for wall in (-WALL_X, WALL_X):
        fig.add_shape(type="line", x0=wall, x1=wall, y0=-0.5, y1=0.5,
                      line=dict(color="#444", width=6))
    for rest in REST_X:      # faint marks at the rest positions
        fig.add_shape(type="line", x0=rest, x1=rest, y0=-0.35, y1=0.35,
                      line=dict(color="#ccc", width=1, dash="dot"))
    fig.update_layout(
        height=230, showlegend=False, updatemenus=menu,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(visible=False, range=[-WALL_X - 0.2, WALL_X + 0.2],
                   fixedrange=True),
        yaxis=dict(visible=False, range=[-0.7, 0.7], fixedrange=True))
    return fig


def trace_figure(times, x1) -> go.Figure:
    """Position of weight 1 against time."""
    fig = go.Figure(go.Scatter(x=times, y=x1, mode="lines",
                               line=dict(color=COLOR_PURE, width=3)))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title="Time",
                      yaxis_title="Weight 1 position (Left − / Right +)",
                      yaxis_range=[-85, 85])
    return fig


def spectrum_figure(omega, amplitude, frequencies) -> go.Figure:
    """The measured spectrum, with the two pattern frequencies labeled."""
    shown = omega <= frequencies[1] + 1.0
    fig = go.Figure(go.Scatter(
        x=omega[shown], y=amplitude[shown], mode="lines", fill="tozeroy",
        line=dict(color=COLOR_NEUTRAL, width=2)))
    for frequency, name, color in [
            (frequencies[0], "Pattern 1", COLOR_STATE0),
            (frequencies[1], "Pattern 2", COLOR_STATE1)]:
        fig.add_vline(x=frequency, line_color=color, line_dash="dash",
                      annotation_text=name, annotation_font_color=color)
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10),
                      xaxis_title="Frequency ω (how fast the jiggle is)",
                      yaxis_title="Amplitude found", yaxis_range=[0, 85])
    return fig


# -----------------------------------------------------------------------------
# Topic 4: a chain of weights
# -----------------------------------------------------------------------------

CHAIN_SCALE = 0.25           # an amplitude of 1 moves a weight 0.25 spacings
RAIL_Y = 1.0                 # height of the rail the side springs hang from


def _chain_shapes(displacements):
    """Coordinates of the weights and all springs for one moment."""
    n = len(displacements)
    masses = np.arange(n) + CHAIN_SCALE * np.asarray(displacements)
    xs, ys = [], []
    for i in range(n - 1):                      # springs between neighbors
        sx, sy = spring_points(masses[i] + 0.12, masses[i + 1] - 0.12, 0,
                               coils=3, half_width=0.1)
        xs += list(sx) + [None]
        ys += list(sy) + [None]
    side_x, side_y = [], []
    for i in range(n):                          # side spring: rail to weight
        side_x += [i, masses[i], None]
        side_y += [RAIL_Y, 0.15, None]
    return masses, xs, ys, side_x, side_y


def chain_animation(frames_u, fine_x, frames_fine_u, nodes=(), loops=12,
                    frame_ms=80, title="") -> go.Figure:
    """
    The chain of weights (top) and its displacement graph (bottom).

    frames_u       one row per frame: displacement of each weight
    fine_x         closely spaced positions for the smooth curve
    frames_fine_u  one row per frame: displacement at each fine_x
    nodes          positions of still points to mark (standing waves only)
    loops          how many times Play runs through the frames
    """
    n = frames_u.shape[1]
    weight_x = np.arange(n)
    limit = max(2.2, float(np.max(np.abs(frames_fine_u))) * 1.1)

    def traces(i):
        masses, xs, ys, side_x, side_y = _chain_shapes(frames_u[i])
        return [
            go.Scatter(x=side_x, y=side_y, mode="lines", hoverinfo="skip",
                       line=dict(color="#bbb", width=1.5), xaxis="x", yaxis="y"),
            go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="skip",
                       line=dict(color=COLOR_NEUTRAL, width=2),
                       xaxis="x", yaxis="y"),
            go.Scatter(x=masses, y=np.zeros(n), mode="markers",
                       hoverinfo="skip", marker=dict(size=20, color=COLOR_PURE),
                       xaxis="x", yaxis="y"),
            go.Scatter(x=fine_x, y=frames_fine_u[i], mode="lines",
                       hoverinfo="skip", line=dict(color=COLOR_NEUTRAL, width=2),
                       xaxis="x", yaxis="y2"),
            go.Scatter(x=weight_x, y=frames_u[i], mode="markers",
                       hoverinfo="skip",
                       marker=dict(size=11, color=frames_u[i],
                                   colorscale=[[0, COLOR_STATE1], [0.5, "#dddddd"],
                                               [1, COLOR_STATE0]],
                                   cmin=-limit, cmax=limit),
                       xaxis="x", yaxis="y2"),
        ]

    names = [str(i) for i in range(len(frames_u))]
    fig = go.Figure(
        data=traces(0),
        frames=[go.Frame(data=traces(i), name=names[i])
                for i in range(len(frames_u))])

    # Play runs through the list of frame names; repeating the names
    # replays the same frames without sending them to the browser again.
    menu = _play_pause(frame_ms)
    menu[0]["buttons"][0]["args"][0] = names * loops

    fig.add_shape(type="line", x0=-0.6, x1=n - 0.4, y0=RAIL_Y, y1=RAIL_Y,
                  xref="x", yref="y", line=dict(color="#444", width=5))
    fig.add_annotation(x=n - 0.4, y=0, xref="x", yref="y", text="Driver",
                       showarrow=False, xanchor="left",
                       font=dict(color=COLOR_STATE1))
    for node in nodes:
        fig.add_shape(type="line", x0=node, x1=node, y0=-limit, y1=limit,
                      xref="x", yref="y2",
                      line=dict(color=COLOR_STATE1, width=1.5, dash="dot"))
    fig.update_layout(
        height=460, showlegend=False, updatemenus=menu,
        margin=dict(l=10, r=40, t=60, b=10),
        title=dict(text=title, x=0.5, y=0.97, font=dict(size=15)),
        xaxis=dict(range=[-0.8, n + 0.3], visible=False, fixedrange=True),
        yaxis=dict(domain=[0.6, 1.0], range=[-0.5, 1.3], visible=False,
                   fixedrange=True),
        yaxis2=dict(domain=[0.0, 0.5], range=[-limit, limit],
                    title="Displacement", fixedrange=True, zeroline=True,
                    zerolinecolor="#ccc"))
    return fig
