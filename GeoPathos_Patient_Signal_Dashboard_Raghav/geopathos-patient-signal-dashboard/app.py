"""GeoPathos Patient Signal Dashboard.

Run locally with: streamlit run app.py
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import (
    COLORS,
    accelerometer_chart,
    correlation_heatmap,
    histogram,
    signal_line_chart,
)
from src.data_utils import (
    DataValidationError,
    correlation_matrix,
    data_quality_notes,
    list_patient_files,
    load_patient_data,
    patient_metadata,
    summary_statistics,
)


st.set_page_config(
    page_title="GeoPathos | Patient Signal Dashboard",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = Path(
    os.getenv("GEOPATHOS_DATA_DIR", APP_DIRECTORY / "data" / "signal_4")
)
PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def inject_styles() -> None:
    """Apply a restrained clinical dashboard theme."""
    st.markdown(
        """
        <style>
            :root {
                --navy: #17324D;
                --teal: #0F9F92;
                --canvas: #F5F8FB;
                --border: #DFE8EF;
            }
            .stApp { background: var(--canvas); }
            [data-testid="stSidebar"] { background: #102A43; }
            [data-testid="stSidebar"] * { color: #F5F8FB; }
            [data-testid="stSidebar"] [data-baseweb="select"] * { color: #102A43; }
            .block-container { max-width: 1480px; padding-top: 2.3rem; padding-bottom: 3rem; }
            h1, h2, h3 { color: var(--navy); letter-spacing: -0.02em; }
            .eyebrow {
                color: var(--teal); font-size: 0.78rem; font-weight: 750;
                letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.35rem;
            }
            .subtitle { color: #5E7184; font-size: 1.02rem; margin-top: -0.55rem; }
            [data-testid="stMetric"] {
                background: #FFFFFF; border: 1px solid var(--border);
                border-radius: 14px; padding: 1rem 1.05rem;
                box-shadow: 0 3px 14px rgba(23, 50, 77, 0.045);
            }
            [data-testid="stMetricLabel"] { color: #60758A; }
            [data-testid="stMetricValue"] { color: var(--navy); }
            [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
                background: #FFFFFF; border: 1px solid var(--border);
                border-radius: 14px; padding: 0.35rem;
                box-shadow: 0 3px 14px rgba(23, 50, 77, 0.035);
            }
            .section-note { color: #64748B; font-size: 0.9rem; margin-top: -0.4rem; }
            div.stDownloadButton > button {
                background: var(--teal); color: #FFFFFF; border: 0;
                border-radius: 10px; font-weight: 700;
            }
            div.stDownloadButton > button:hover {
                background: #0B8279; color: #FFFFFF; border: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_patient_data(file_path: str, modified_time_ns: int) -> pd.DataFrame:
    """Load a patient file once and refresh automatically when it changes."""
    del modified_time_ns
    return load_patient_data(Path(file_path))


def format_duration(seconds: float) -> str:
    minutes, remaining_seconds = divmod(int(round(seconds)), 60)
    return f"{minutes}m {remaining_seconds:02d}s"


def render_header() -> None:
    st.markdown('<div class="eyebrow">GeoPathos · PhysioPain</div>', unsafe_allow_html=True)
    st.title("Patient Signal Dashboard")
    st.markdown(
        '<p class="subtitle">Explore physiological signals sampled at 4 Hz across individual headache recordings.</p>',
        unsafe_allow_html=True,
    )


def render_sidebar(patient_files: list[Path]) -> Path:
    with st.sidebar:
        st.markdown("## Signal explorer")
        st.caption("Select one processed patient recording.")
        selected_name = st.selectbox(
            "Patient CSV file",
            options=[path.name for path in patient_files],
            index=0,
        )
        st.markdown("---")
        st.markdown("**Dataset**")
        st.caption(f"{len(patient_files)} patients · 4 samples/second")
        st.caption("Channels: BVP, EDA, temperature and 3-axis accelerometer")
        st.markdown("---")
        st.caption("Source values are displayed as supplied and are not silently altered.")
    return next(path for path in patient_files if path.name == selected_name)


def render_patient_metrics(frame: pd.DataFrame) -> None:
    metadata = patient_metadata(frame)
    columns = st.columns(5)
    values = (
        ("Patient ID", metadata.patient_id),
        ("Pain type", metadata.pain_type),
        ("Pain scale", metadata.pain_scale),
        ("Total samples", f"{metadata.total_samples:,}"),
        ("Recording duration", format_duration(metadata.duration_seconds)),
    )
    for column, (label, value) in zip(columns, values):
        column.metric(label, value)


def render_overview(full_frame: pd.DataFrame, chart_frame: pd.DataFrame) -> None:
    st.subheader("Signal timelines")
    st.markdown(
        '<p class="section-note">Hover to inspect exact values. Drag across a chart to zoom into a time interval.</p>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            signal_line_chart(
                chart_frame, "bvp", "BVP vs Time", "BVP", COLORS["blue"]
            ),
            width="stretch",
            config=PLOT_CONFIG,
        )
    with right:
        st.plotly_chart(
            signal_line_chart(
                chart_frame, "eda", "EDA vs Time", "EDA", COLORS["teal"]
            ),
            width="stretch",
            config=PLOT_CONFIG,
        )

    left, right = st.columns([1, 1.45])
    with left:
        st.plotly_chart(
            signal_line_chart(
                chart_frame,
                "temperature",
                "Temperature vs Time",
                "Temperature (°C)",
                COLORS["rose"],
            ),
            width="stretch",
            config=PLOT_CONFIG,
        )
    with right:
        st.plotly_chart(
            accelerometer_chart(chart_frame),
            width="stretch",
            config=PLOT_CONFIG,
        )

    st.subheader("Summary statistics")
    st.markdown(
        '<p class="section-note">Calculated from the complete selected recording.</p>',
        unsafe_allow_html=True,
    )
    formatted_summary = summary_statistics(full_frame).style.format("{:.3f}")
    st.dataframe(formatted_summary, width="stretch")


def render_distributions(frame: pd.DataFrame) -> None:
    st.subheader("Signal distributions")
    st.markdown(
        '<p class="section-note">Histograms and correlations use the complete selected recording.</p>',
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    chart_specs = (
        ("bvp", "BVP Histogram", "BVP", COLORS["blue"]),
        ("eda", "EDA Histogram", "EDA", COLORS["teal"]),
        (
            "temperature",
            "Temperature Histogram",
            "Temperature (°C)",
            COLORS["rose"],
        ),
    )
    for container, (column, title, x_axis, color) in zip(columns, chart_specs):
        with container:
            st.plotly_chart(
                histogram(frame, column, title, x_axis, color),
                width="stretch",
                config=PLOT_CONFIG,
            )

    st.plotly_chart(
        correlation_heatmap(correlation_matrix(frame)),
        width="stretch",
        config=PLOT_CONFIG,
    )
    st.caption("The heatmap shows Pearson correlation coefficients from −1 to +1.")


def render_data_table(frame: pd.DataFrame, selected_file: Path) -> None:
    st.subheader("Complete patient data")
    st.markdown(
        '<p class="section-note">The derived time column is included in both the table and downloaded CSV.</p>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download selected patient CSV",
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_file.stem}_with_time.csv",
        mime="text/csv",
        width="content",
    )
    st.dataframe(
        frame,
        width="stretch",
        height=570,
        hide_index=True,
        column_config={
            "time_seconds": st.column_config.NumberColumn("Time (seconds)", format="%.2f"),
            "temperature": st.column_config.NumberColumn("Temperature (°C)", format="%.2f"),
        },
    )


def main() -> None:
    inject_styles()
    render_header()

    try:
        patient_files = list_patient_files(DATA_DIRECTORY)
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info(
            "Place patient CSV files in data/signal_4 or set the GEOPATHOS_DATA_DIR environment variable."
        )
        st.stop()

    selected_file = render_sidebar(patient_files)
    try:
        frame = cached_patient_data(
            str(selected_file), selected_file.stat().st_mtime_ns
        )
    except (DataValidationError, OSError) as exc:
        st.error(f"Unable to display {selected_file.name}: {exc}")
        st.stop()

    render_patient_metrics(frame)

    notes = data_quality_notes(frame)
    if notes:
        with st.expander("Data quality note", expanded=False):
            for note in notes:
                st.info(note)

    max_second = max(1, math.ceil(float(frame["time_seconds"].iloc[-1])))
    with st.sidebar:
        st.markdown("**Chart time window**")
        selected_range = st.slider(
            "Seconds",
            min_value=0,
            max_value=max_second,
            value=(0, max_second),
            step=1,
            label_visibility="collapsed",
        )
        st.caption(f"Showing {selected_range[0]}s to {selected_range[1]}s")

    chart_frame = frame.loc[
        frame["time_seconds"].between(selected_range[0], selected_range[1])
    ]

    st.markdown("")
    overview_tab, distribution_tab, data_tab = st.tabs(
        ["Overview", "Distributions & correlation", "Patient data"]
    )
    with overview_tab:
        render_overview(frame, chart_frame)
    with distribution_tab:
        render_distributions(frame)
    with data_tab:
        render_data_table(frame, selected_file)


if __name__ == "__main__":
    main()
