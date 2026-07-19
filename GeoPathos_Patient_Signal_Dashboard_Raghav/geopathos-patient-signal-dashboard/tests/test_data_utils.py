"""Unit tests for the dashboard's data layer."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data_utils import (
    DataValidationError,
    correlation_matrix,
    load_patient_data,
    patient_metadata,
    summary_statistics,
)


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bvp": [1.0, 2.0, 3.0],
            "eda": [0.1, 0.2, 0.3],
            "x": [10.0, 11.0, 12.0],
            "y": [20.0, 21.0, 22.0],
            "z": [30.0, 31.0, 32.0],
            "temperature": [36.5, 36.6, 36.7],
            "pain_scale": [3, 3, 3],
            "pain_type": ["headache"] * 3,
            "person_id": ["S001"] * 3,
        }
    )


class DataUtilsTests(unittest.TestCase):
    def write_csv(self, frame: pd.DataFrame) -> tuple[tempfile.TemporaryDirectory, Path]:
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "S001_4Hz.csv"
        frame.to_csv(path, index=False)
        return directory, path

    def test_load_adds_time_at_four_hertz(self) -> None:
        directory, path = self.write_csv(valid_frame())
        self.addCleanup(directory.cleanup)

        loaded = load_patient_data(path)

        self.assertEqual(loaded["time_seconds"].tolist(), [0.0, 0.25, 0.5])

    def test_metadata_matches_patient_record(self) -> None:
        directory, path = self.write_csv(valid_frame())
        self.addCleanup(directory.cleanup)
        metadata = patient_metadata(load_patient_data(path))

        self.assertEqual(metadata.patient_id, "S001")
        self.assertEqual(metadata.pain_type, "Headache")
        self.assertEqual(metadata.pain_scale, "3")
        self.assertEqual(metadata.total_samples, 3)
        self.assertEqual(metadata.duration_seconds, 0.5)

    def test_summary_contains_required_statistics(self) -> None:
        directory, path = self.write_csv(valid_frame())
        self.addCleanup(directory.cleanup)
        summary = summary_statistics(load_patient_data(path))

        self.assertEqual(
            summary.columns.tolist(),
            ["Mean", "Minimum", "Maximum", "Standard deviation"],
        )
        self.assertAlmostEqual(summary.loc["BVP", "Mean"], 2.0)

    def test_correlation_contains_all_six_signals(self) -> None:
        directory, path = self.write_csv(valid_frame())
        self.addCleanup(directory.cleanup)
        matrix = correlation_matrix(load_patient_data(path))

        self.assertEqual(matrix.shape, (6, 6))
        self.assertEqual(matrix.columns.tolist(), ["BVP", "EDA", "Temperature", "X", "Y", "Z"])

    def test_missing_column_is_rejected(self) -> None:
        frame = valid_frame().drop(columns="eda")
        directory, path = self.write_csv(frame)
        self.addCleanup(directory.cleanup)

        with self.assertRaisesRegex(DataValidationError, "eda"):
            load_patient_data(path)

    def test_non_numeric_signal_is_rejected(self) -> None:
        frame = valid_frame()
        frame["bvp"] = frame["bvp"].astype(object)
        frame.loc[1, "bvp"] = "not-a-number"
        directory, path = self.write_csv(frame)
        self.addCleanup(directory.cleanup)

        with self.assertRaisesRegex(DataValidationError, "non-numeric"):
            load_patient_data(path)


if __name__ == "__main__":
    unittest.main()
