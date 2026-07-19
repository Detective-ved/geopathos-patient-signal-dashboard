"""Plotly chart builders for the GeoPathos dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


COLORS = {
    "navy": "#17324D",
    "blue": "#2B7A9B",
    "teal": "#14B8A6",
    "amber": "#F59E0B",
    "purple": "#7C3AED",
    "rose": "#E85D75",
    "muted": "#64748B",
    "grid": "#E8EEF4",
}


def _base_layout(title: str, y_axis_title: str) -> dict:
    return {
        "title": {"text": title, "x": 0.01, "xanchor": "left"},
        "height": 330,
        "margin": {"l": 24, "r": 20, "t": 56, "b": 30},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#FFFFFF",
        "font": {"family": "Inter, Arial, sans-serif", "color": COLORS["navy"]},
        "hovermode": "x unified",
        "xaxis": {
            "title": "Time (seconds)",
            "showgrid": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
        },
        "yaxis": {
            "title": y_axis_title,
            "showgrid": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
        },
        "legend": {"orientation": "h", "y": 1.12, "x": 1, "xanchor": "right"},
    }


def signal_line_chart(
    frame: pd.DataFrame,
    column: str,
    title: str,
    y_axis_title: str,
    color: str,
) -> go.Figure:
    """Build an interactive single-signal time-series chart."""
    figure = go.Figure(
        go.Scattergl(
            x=frame["time_seconds"],
            y=frame[column],
            mode="lines",
            name=title,
            line={"color": color, "width": 1.5},
            hovertemplate="%{y:.3f}<extra></extra>",
        )
    )
    figure.update_layout(**_base_layout(title, y_axis_title))
    return figure


def accelerometer_chart(frame: pd.DataFrame) -> go.Figure:
    """Build the required combined X, Y, and Z accelerometer chart."""
    figure = go.Figure()
    for column, label, color in (
        ("x", "X", COLORS["blue"]),
        ("y", "Y", COLORS["amber"]),
        ("z", "Z", COLORS["purple"]),
    ):
        figure.add_trace(
            go.Scattergl(
                x=frame["time_seconds"],
                y=frame[column],
                mode="lines",
                name=label,
                line={"color": color, "width": 1.25},
                hovertemplate=f"{label}: %{{y:.3f}}<extra></extra>",
            )
        )
    figure.update_layout(**_base_layout("Accelerometer X, Y and Z vs Time", "Acceleration"))
    figure.update_layout(height=380)
    return figure


def histogram(
    frame: pd.DataFrame,
    column: str,
    title: str,
    x_axis_title: str,
    color: str,
) -> go.Figure:
    """Build a signal distribution histogram."""
    figure = go.Figure(
        go.Histogram(
            x=frame[column],
            nbinsx=45,
            marker={"color": color, "line": {"color": "#FFFFFF", "width": 0.35}},
            hovertemplate="Range: %{x}<br>Samples: %{y}<extra></extra>",
        )
    )
    figure.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left"},
        height=330,
        margin={"l": 24, "r": 20, "t": 56, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font={"family": "Inter, Arial, sans-serif", "color": COLORS["navy"]},
        bargap=0.04,
        xaxis={"title": x_axis_title, "gridcolor": COLORS["grid"], "zeroline": False},
        yaxis={"title": "Sample count", "gridcolor": COLORS["grid"], "zeroline": False},
    )
    return figure


def correlation_heatmap(matrix: pd.DataFrame) -> go.Figure:
    """Build an annotated correlation heatmap."""
    figure = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, "#9F1239"],
                [0.5, "#F8FAFC"],
                [1.0, COLORS["teal"]],
            ],
            text=matrix.round(2).values,
            texttemplate="%{text}",
            hovertemplate="%{y} vs %{x}<br>r = %{z:.3f}<extra></extra>",
            colorbar={"title": "Pearson r", "thickness": 14},
        )
    )
    figure.update_layout(
        title={"text": "Signal Correlation Heatmap", "x": 0.01, "xanchor": "left"},
        height=470,
        margin={"l": 40, "r": 20, "t": 60, "b": 35},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Arial, sans-serif", "color": COLORS["navy"]},
        xaxis={"side": "bottom"},
        yaxis={"autorange": "reversed"},
    )
    return figure

