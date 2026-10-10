"""
components/plots.py — Plotly drawing helpers shared by the pages
================================================================

Nothing here does physics. Each function takes numbers that were already
calculated (in the physics/ folder) and draws them.
"""

import numpy as np
import plotly.graph_objects as go

from components.theme import (COLOR_AXIS, COLOR_MIX, COLOR_NEUTRAL,
                              COLOR_PURE, COLOR_STATE0, COLOR_STATE1)
from physics.mixture import probability_plus, unit_vector

# Labels at the ends of the Bloch sphere's axes.
QUBIT_LABELS = {"|0⟩": (0, 0, 1.2), "|1⟩": (0, 0, -1.2),
                "|+⟩ (x)": (1.25, 0, 0), "|+i⟩ (y)": (0, 1.25, 0)}


# -----------------------------------------------------------------------------
# Bloch sphere
# -----------------------------------------------------------------------------

def arrow(fig, vec, color, name):
    """Draw a vector from the origin as a line with a cone for the arrowhead."""
    fig.add_trace(go.Scatter3d(
        x=[0, vec[0]], y=[0, vec[1]], z=[0, vec[2]],
        mode="lines", line=dict(color=color, width=7), name=name,
    ))
    if np.linalg.norm(vec) > 0.05:   # skip arrowhead for (near) zero vectors
        fig.add_trace(go.Cone(
            x=[vec[0]], y=[vec[1]], z=[vec[2]],
            u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=0.15, anchor="tip",
            colorscale=[[0, color], [1, color]], showscale=False,
            showlegend=False,
        ))


def bloch_sphere_base(labels=None, height=460) -> go.Figure:
    """An empty Bloch sphere: translucent ball, three axes, and end labels."""
    labels = QUBIT_LABELS if labels is None else labels
    fig = go.Figure()

    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
    fig.add_trace(go.Surface(
        x=np.cos(u) * np.sin(v), y=np.sin(u) * np.sin(v), z=np.cos(v),
        opacity=0.08, showscale=False, hoverinfo="skip",
        colorscale=[[0, "#888"], [1, "#888"]],
    ))

    for a, b in [((-1, 0, 0), (1, 0, 0)), ((0, -1, 0), (0, 1, 0)),
                 ((0, 0, -1), (0, 0, 1))]:
        fig.add_trace(go.Scatter3d(
            x=[a[0], b[0]], y=[a[1], b[1]], z=[a[2], b[2]], mode="lines",
            line=dict(color="#aaa", width=2), showlegend=False,
            hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(
        x=[p[0] for p in labels.values()], y=[p[1] for p in labels.values()],
        z=[p[2] for p in labels.values()], mode="text",
        text=list(labels.keys()), showlegend=False, hoverinfo="skip"))

    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.02),
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False), aspectmode="cube",
            camera=dict(eye=dict(x=1.4, y=1.1, z=0.7)),
        ),
    )
    return fig


def bloch_sphere_figure(r_pure, r_mix, n_axis) -> go.Figure:
    """3D Bloch sphere with both state vectors and the measurement axis."""
    fig = bloch_sphere_base()
    # Measurement axis drawn as a dashed line through the whole sphere
    fig.add_trace(go.Scatter3d(
        x=[-n_axis[0], n_axis[0]], y=[-n_axis[1], n_axis[1]],
        z=[-n_axis[2], n_axis[2]], mode="lines",
        line=dict(color=COLOR_AXIS, width=4, dash="dash"),
        name="Measurement axis"))
    arrow(fig, r_pure, COLOR_PURE, "Superposition (on the surface)")
    arrow(fig, r_mix, COLOR_MIX, "Mixture (inside the sphere)")
    return fig


def results_figure(plus_pure, plus_mix, n_shots) -> go.Figure:
    """Bar chart of simulated '+' and '-' counts for both states."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Superposition", x=["+", "−"],
                         y=[plus_pure, n_shots - plus_pure],
                         marker_color=COLOR_PURE))
    fig.add_trace(go.Bar(name="Mixture", x=["+", "−"],
                         y=[plus_mix, n_shots - plus_mix],
                         marker_color=COLOR_MIX))
    fig.update_layout(barmode="group", height=320,
                      yaxis_title="Number of shots",
                      xaxis_title="Measurement outcome",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def sweep_figure(r_pure, r_mix, meas_azimuth, current_polar) -> go.Figure:
    """
    P(+) as the measurement axis tilts from +z (0 deg) to -z (180 deg).
    This shows at a glance where the two states agree and where they differ.
    """
    angles = np.linspace(0, 180, 181)
    p_pure = [probability_plus(r_pure, unit_vector(a, meas_azimuth))
              for a in angles]
    p_mix = [probability_plus(r_mix, unit_vector(a, meas_azimuth))
             for a in angles]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=angles, y=p_pure, name="Superposition",
                             line=dict(color=COLOR_PURE, width=3)))
    fig.add_trace(go.Scatter(x=angles, y=p_mix, name="Mixture",
                             line=dict(color=COLOR_MIX, width=3, dash="dot")))
    fig.add_vline(x=current_polar, line_color=COLOR_AXIS, line_dash="dash",
                  annotation_text="your axis")
    fig.update_layout(height=320, yaxis_range=[-0.02, 1.02],
                      xaxis_title="Measurement axis tilt from +z (degrees)",
                      yaxis_title="P(+)",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def matrix_latex(m: np.ndarray) -> str:
    """Format a 2x2 complex matrix as LaTeX, hiding zero imaginary parts."""
    def fmt(z):
        re, im = round(z.real, 3), round(z.imag, 3)
        if abs(im) < 1e-3:
            return f"{re:.3f}"
        sign = "+" if im >= 0 else "-"
        return f"{re:.3f} {sign} {abs(im):.3f}i"
    return (r"\begin{pmatrix}" + f"{fmt(m[0,0])} & {fmt(m[0,1])} \\\\ "
            f"{fmt(m[1,0])} & {fmt(m[1,1])}" + r"\end{pmatrix}")


# -----------------------------------------------------------------------------
# Small charts shared by the topic pages
# -----------------------------------------------------------------------------

def count_bars(labels, counts, colors=(COLOR_STATE0, COLOR_STATE1),
               y_title="Count", height=260) -> go.Figure:
    """Bar chart of counts (heads/tails, UP/DOWN) with the number on each bar."""
    fig = go.Figure(go.Bar(x=list(labels), y=list(counts),
                           marker_color=list(colors),
                           text=[str(c) for c in counts], textposition="auto"))
    fig.update_layout(height=height, yaxis_title=y_title,
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def spring_points(x_start, x_end, y, coils=8, half_width=0.25):
    """
    Points of a zigzag line from x_start to x_end at height y, so a spring
    visibly stretches and squeezes as its ends move. Returns (xs, ys).
    """
    xs = np.linspace(x_start, x_end, 2 * coils + 3)
    ys = np.full(xs.shape, float(y))
    # Leave the first and last points on the axis; alternate the rest.
    ys[1:-1] += half_width * np.where(np.arange(len(xs) - 2) % 2 == 0, 1, -1)
    return xs, ys
