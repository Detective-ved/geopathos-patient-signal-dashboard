# GeoPathos Patient Signal Dashboard

A Streamlit dashboard for exploring patient-level physiological recordings from the processed PhysioPain `signal_4` dataset. Each recording is sampled at 4 Hz and includes BVP, EDA, temperature, and three-axis accelerometer signals.

## Features

- Patient CSV selection from a dropdown
- Patient ID, pain type, pain scale, sample count, and recording duration
- Correct zero-based time axis calculated as `row number / 4`
- Interactive BVP, EDA, temperature, and combined X/Y/Z time-series charts
- Mean, minimum, maximum, and standard deviation for every signal
- BVP, EDA, and temperature histograms
- Annotated Pearson correlation heatmap
- Complete patient data table with the derived time column
- CSV download for the selected patient
- Clear validation messages for malformed or incomplete files
- Optional chart time-window control without changing full-record statistics

## Project structure

```text
geopathos-patient-signal-dashboard/
├── app.py
├── data/
│   └── signal_4/             # 27 supplied patient CSV files
├── src/
│   ├── __init__.py
│   ├── charts.py             # Plotly chart builders
│   └── data_utils.py         # Validation, time axis, metadata, statistics
├── tests/
│   └── test_data_utils.py
├── .streamlit/
│   └── config.toml
├── .gitignore
├── README.md
└── requirements.txt
```

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies and launch the app:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, normally `http://localhost:8501`.

## Run tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

The tests cover the 4 Hz time calculation, metadata extraction, summary statistics, correlation shape, and invalid-file handling.

## Data expectations

Every patient CSV must contain these columns:

```text
bvp, eda, x, y, z, temperature, pain_scale, pain_type, person_id
```

The included dataset contains 27 patient files and 138,154 total samples. Source values are displayed and downloaded unchanged. The only added field is `time_seconds`, calculated as:

```text
time_seconds = zero_based_row_number / 4
```

To point the app to another folder with the same CSV schema, set `GEOPATHOS_DATA_DIR` before starting Streamlit.

## Future live-data integration

The visualization layer is separated from the CSV data layer. A future integration can replace `load_patient_data()` with a live BVP/GSR/temperature stream adapter that returns the same columns. Patient cards, charts, statistics, and the dashboard layout can remain unchanged.

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, select the repository and branch.
3. Set the main file path to `app.py`.
4. Deploy. No secrets are required for the bundled CSV dataset.

