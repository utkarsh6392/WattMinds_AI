
import pandas as pd
from pathlib import Path

# Step 1: Define project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "hourly_energy_data.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "ml_ready_dataset.csv"
REPORT_FILE = PROJECT_ROOT / "outputs" / "ml_dataset_preparation_report.txt"

# Step 2: Check input file
if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Hourly dataset not found: {INPUT_FILE}"
    )

# Step 3: Load hourly dataset
df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)
print("\nOriginal columns:")
print(df.columns.tolist())

# Step 4: Validate required columns
required_columns = ["Hour", "Energy_kWh"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns missing: {missing_columns}"
    )

# Step 5: Convert Hour into datetime
df["Hour"] = pd.to_datetime(df["Hour"], errors="coerce")

df["Energy_kWh"] = pd.to_numeric(
    df["Energy_kWh"], errors="coerce"
)

# Step 6: Clean invalid timestamps and duplicate timestamps
df = df.dropna(subset=["Hour"])
df = df.sort_values("Hour")

duplicate_count = int(df["Hour"].duplicated().sum())

df = df.drop_duplicates(subset=["Hour"], keep="first")
df = df.set_index("Hour")

# Step 7: Create a continuous hourly timeline
# Missing hours remain NaN. We do NOT invent energy readings.
hourly_index = pd.date_range(
    start=df.index.min(),
    end=df.index.max(),
    freq="h"
)

df = df.reindex(hourly_index)
df.index.name = "Hour"

energy = df["Energy_kWh"]

# Step 8: Create time-based features
ml_df = pd.DataFrame(index=df.index)

ml_df["Hour_of_Day"] = df.index.hour
ml_df["Day_of_Week"] = df.index.dayofweek
ml_df["Day_of_Month"] = df.index.day
ml_df["Month"] = df.index.month
ml_df["Is_Weekend"] = (
    df.index.dayofweek >= 5
).astype(int)

# Step 9: Create past-energy features
# Shift ensures only past readings are used as inputs.
ml_df["Lag_1h"] = energy.shift(1)
ml_df["Lag_2h"] = energy.shift(2)
ml_df["Lag_24h"] = energy.shift(24)

# Rolling averages use past hours only, avoiding data leakage.
past_energy = energy.shift(1)

ml_df["Rolling_Mean_3h"] = past_energy.rolling(
    window=3,
    min_periods=3
).mean()

ml_df["Rolling_Mean_24h"] = past_energy.rolling(
    window=24,
    min_periods=24
).mean()

# Step 10: Define target as energy in the NEXT hour
ml_df["Target_Next_Hour_kWh"] = energy.shift(-1)

# Step 11: Remove rows with missing features or target
# This also removes rows affected by missing hourly readings.
rows_before = len(ml_df)

ml_df = ml_df.dropna()

rows_after = len(ml_df)
rows_removed = rows_before - rows_after

# Step 12: Validate final dataset
if ml_df.empty:
    raise ValueError(
        "ML dataset is empty. Check the hourly input data."
    )

if ml_df.isna().any().any():
    raise ValueError(
        "Missing values remain in the ML dataset."
    )

if not ml_df.index.is_monotonic_increasing:
    raise ValueError(
        "Timestamps are not in chronological order."
    )

# Step 13: Save ML-ready dataset
ml_df = ml_df.reset_index()

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

ml_df.to_csv(OUTPUT_FILE, index=False)

# Step 14: Prepare a chronological 80/20 split summary
# Actual splitting and model training will be done later.
split_index = int(len(ml_df) * 0.8)

train_rows = split_index
test_rows = len(ml_df) - split_index

# Step 15: Save preparation report
report = f"""
WATTMinds - ML DATASET PREPARATION REPORT

Input file:
{INPUT_FILE.name}

Output file:
{OUTPUT_FILE.name}

Original hourly rows:
{len(hourly_index) if False else rows_before}

Rows removed due to missing features/target:
{rows_removed}

Final ML-ready rows:
{len(ml_df)}

Number of input features:
{len(ml_df.columns) - 2}

Feature columns:
{ml_df.columns.tolist()[1:-1]}

Target column:
Target_Next_Hour_kWh

Chronological 80/20 split summary:
Training rows: {train_rows}
Testing rows: {test_rows}

First timestamp:
{ml_df['Hour'].min()}

Last timestamp:
{ml_df['Hour'].max()}

Missing values remaining:
{int(ml_df.isna().sum().sum())}

Duplicate timestamps removed:
{duplicate_count}

Note:
Missing hourly energy readings were not interpolated.
Rolling features use past readings only.
The target is energy consumption in the next hour.
No model has been trained in this step.
"""

REPORT_FILE.write_text(report, encoding="utf-8")

# Step 16: Display results
print("\n========== ML DATASET PREPARATION ==========")
print("Final dataset shape:", ml_df.shape)

print("\nFirst 5 rows:")
print(ml_df.head())

print("\nMissing values:")
print(ml_df.isna().sum())

print("\nTarget summary:")
print(ml_df["Target_Next_Hour_kWh"].describe())

print("\nChronological split summary:")
print("Training rows (80%):", train_rows)
print("Testing rows (20%):", test_rows)

print("\nSaved dataset:", OUTPUT_FILE)
print("Saved report:", REPORT_FILE)

print("\nML DATASET PREPARATION COMPLETED SUCCESSFULLY!")
