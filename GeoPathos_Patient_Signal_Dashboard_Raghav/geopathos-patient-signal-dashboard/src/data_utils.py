"""Data loading, validation, metadata, and statistics helpers.

Keeping these functions independent from Streamlit makes the data layer easy to
test and allows the dashboard to switch to a live sensor source in the future.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


SAMPLING_FREQUENCY_HZ = 4.0
SIGNAL_COLUMNS = ("bvp", "eda", "temperature", "x", "y", "z")
REQUIRED_COLUMNS = SIGNAL_COLUMNS + ("pain_scale", "pain_type", "person_id")


class DataValidationError(ValueError):
    """Raised when a patient CSV does not match the expected signal schema."""


@dataclass(frozen=True)
class PatientMetadata:
    """Patient-level values displayed in the dashboard header."""

    patient_id: str
    pain_type: str
    pain_scale: str
    total_samples: int
    duration_seconds: float


def list_patient_files(data_directory: Path) -> list[Path]:
    """Return patient CSV files in a deterministic, case-insensitive order."""
    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_directory}")

    files = sorted(
        (path for path in data_directory.iterdir() if path.suffix.lower() == ".csv"),
        key=lambda path: path.name.casefold(),
    )
    if not files:
        raise FileNotFoundError(f"No CSV files found in: {data_directory}")
    return files


def load_patient_data(
    csv_path: Path, sampling_frequency_hz: float = SAMPLING_FREQUENCY_HZ
) -> pd.DataFrame:
    """Load and validate one patient CSV and add a zero-based time column.

    The source values are never cleaned or replaced silently. Invalid schemas,
    empty files, and non-numeric signal values result in a clear validation
    error that the UI can display to the user.
    """
    if sampling_frequency_hz <= 0:
        raise ValueError("Sampling frequency must be greater than zero.")
    if csv_path.suffix.lower() != ".csv":
        raise DataValidationError("The selected file must be a CSV file.")

    try:
        frame = pd.read_csv(csv_path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DataValidationError(f"Could not read {csv_path.name}: {exc}") from exc

    if frame.empty:
        raise DataValidationError(f"{csv_path.name} contains no patient samples.")

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise DataValidationError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    frame = frame.loc[:, list(REQUIRED_COLUMNS)].copy()

    for column in (*SIGNAL_COLUMNS, "pain_scale"):
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid_count = int((converted.isna() & frame[column].notna()).sum())
        if invalid_count:
            raise DataValidationError(
                f"Column '{column}' contains {invalid_count} non-numeric value(s)."
            )
        if converted.isna().any():
            raise DataValidationError(f"Column '{column}' contains missing values.")
        frame[column] = converted

    for column in ("pain_type", "person_id"):
        if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            raise DataValidationError(f"Column '{column}' contains missing values.")
        frame[column] = frame[column].astype(str).str.strip()

    frame.insert(
        0,
        "time_seconds",
        np.arange(len(frame), dtype=float) / float(sampling_frequency_hz),
    )
    return frame


def _display_unique(series: pd.Series) -> str:
    """Format a patient-level value, while making mixed metadata explicit."""
    values = series.dropna().unique().tolist()
    if not values:
        return "Not available"
    if len(values) > 1:
        return "Mixed"
    value = values[0]
    if isinstance(value, (int, float, np.integer, np.floating)) and float(value).is_integer():
        return str(int(value))
    return str(value)


def patient_metadata(frame: pd.DataFrame) -> PatientMetadata:
    """Extract the patient information required by the task brief."""
    duration = float(frame["time_seconds"].iloc[-1]) if len(frame) > 1 else 0.0
    return PatientMetadata(
        patient_id=_display_unique(frame["person_id"]),
        pain_type=_display_unique(frame["pain_type"]).title(),
        pain_scale=_display_unique(frame["pain_scale"]),
        total_samples=len(frame),
        duration_seconds=duration,
    )


def summary_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate the required statistics for every physiological signal."""
    summary = frame.loc[:, SIGNAL_COLUMNS].agg(["mean", "min", "max", "std"]).T
    summary.columns = ["Mean", "Minimum", "Maximum", "Standard deviation"]
    summary.index = [
        "BVP",
        "EDA",
        "Temperature",
        "Accelerometer X",
        "Accelerometer Y",
        "Accelerometer Z",
    ]
    summary.index.name = "Signal"
    return summary


def correlation_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    """Return Pearson correlations for the six numeric signal channels."""
    matrix = frame.loc[:, SIGNAL_COLUMNS].corr()
    labels = ["BVP", "EDA", "Temperature", "X", "Y", "Z"]
    matrix.index = labels
    matrix.columns = labels
    return matrix


def data_quality_notes(frame: pd.DataFrame) -> list[str]:
    """Report suspicious values without mutating the supplied dataset."""
    notes: list[str] = []
    temperature_outliers = int(
        ((frame["temperature"] < 20) | (frame["temperature"] > 45)).sum()
    )
    if temperature_outliers:
        notes.append(
            f"{temperature_outliers:,} temperature sample(s) fall outside 20–45 °C. "
            "They remain unchanged in all views and downloads."
        )
    return notes

