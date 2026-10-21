
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# STEP 1: Load cleaned dataset
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "household_power_consumption_cleaned.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

# --------------------------------------------------
# STEP 2: Identify and parse the date/time columns
# --------------------------------------------------

if "Datetime" in df.columns:
    df["Datetime"] = pd.to_datetime(
        df["Datetime"], dayfirst=True, errors="coerce"
    )

elif "Date" in df.columns and "Time" in df.columns:
    df["Datetime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        dayfirst=True,
        errors="coerce"
    )

elif "Date" in df.columns:
    df["Datetime"] = pd.to_datetime(
        df["Date"], dayfirst=True, errors="coerce"
    )

else:
    raise ValueError(
        "Date/time column nahi mila. Check your dataset column names."
    )

# --------------------------------------------------
# STEP 3: Validate required columns
# --------------------------------------------------

required_columns = [
    "Global_active_power",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Dataset mein ye columns missing hain: {missing_columns}"
    )

# Convert readings to numeric values
for col in required_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --------------------------------------------------
# STEP 4: Filter August 2008
# --------------------------------------------------

august = df[
    (df["Datetime"] >= "2008-08-01") &
    (df["Datetime"] < "2008-09-01")
].copy()

august = august.dropna(
    subset=["Datetime"] + required_columns
)

if august.empty:
    raise ValueError(
        "August 2008 ka data nahi mila. Check the date format and dataset."
    )

# Original dataset measurements are minute-level:
# Global_active_power is in kW.
# Sub-meter readings are in Wh per minute.
# Hourly energy = sum(Global_active_power) / 60.
# Hourly sub-meter energy = sum(sub-meter readings) / 1000.

august = august.set_index("Datetime").sort_index()

hourly = august.resample("h").agg({
    "Global_active_power": "sum",
    "Sub_metering_1": "sum",
    "Sub_metering_2": "sum",
    "Sub_metering_3": "sum"
})

# Calculate energy for each hour
hourly["Energy_kWh"] = (
    hourly["Global_active_power"] / 60
)

hourly["Sub_metering_1_kWh"] = (
    hourly["Sub_metering_1"] / 1000
)

hourly["Sub_metering_2_kWh"] = (
    hourly["Sub_metering_2"] / 1000
)

hourly["Sub_metering_3_kWh"] = (
    hourly["Sub_metering_3"] / 1000
)

# Count raw readings in each hour to identify incomplete hours
hourly["Available_Minutes"] = (
    august["Global_active_power"].resample("h").count()
)

hourly["Complete_Hour"] = (
    hourly["Available_Minutes"] == 60
)

# Keep complete hours for fair comparison
hourly = hourly[hourly["Complete_Hour"]].copy()

if hourly.empty:
    raise ValueError(
        "August 2008 mein koi complete 60-minute hour nahi mila."
    )

# --------------------------------------------------
# STEP 5: Identify unusually high energy readings
# --------------------------------------------------

threshold_95 = hourly["Energy_kWh"].quantile(0.95)
threshold_99 = hourly["Energy_kWh"].quantile(0.99)

hourly["Above_95th"] = (
    hourly["Energy_kWh"] > threshold_95
)

hourly["Above_99th"] = (
    hourly["Energy_kWh"] > threshold_99
)

# --------------------------------------------------
# STEP 6: Print highest-energy hours and sub-meters
# --------------------------------------------------

columns_to_show = [
    "Energy_kWh",
    "Sub_metering_1_kWh",
    "Sub_metering_2_kWh",
    "Sub_metering_3_kWh",
    "Available_Minutes",
    "Above_95th",
    "Above_99th"
]

print("\nAUGUST 2008 SUB-METER ANOMALY VALIDATION")
print("=" * 90)

print(f"Complete hourly records: {len(hourly)}")
print(f"95th percentile threshold: {threshold_95:.3f} kWh")
print(f"99th percentile threshold: {threshold_99:.3f} kWh")

print("\nTOP 15 HIGHEST-ENERGY HOURS")
print("-" * 90)

top_hours = hourly.sort_values(
    "Energy_kWh", ascending=False
).head(15)

print(top_hours[columns_to_show].round(3).to_string())

# --------------------------------------------------
# STEP 7: Compare high-energy hours with normal hours
# --------------------------------------------------

hourly["Reading_Type"] = np.where(
    hourly["Above_95th"],
    "High energy (above 95th percentile)",
    "Normal-range energy"
)

submeter_columns = [
    "Sub_metering_1_kWh",
    "Sub_metering_2_kWh",
    "Sub_metering_3_kWh"
]

comparison = hourly.groupby("Reading_Type")[
    ["Energy_kWh"] + submeter_columns
].mean()

print("\nAVERAGE READINGS: HIGH-ENERGY VS NORMAL-RANGE HOURS")
print("-" * 90)
print(comparison.round(3).to_string())

# --------------------------------------------------
# STEP 8: Save detailed report
# --------------------------------------------------

report_path = OUTPUT_DIR / "august_submeter_anomaly_validation.csv"

hourly.reset_index().to_csv(report_path, index=False)

comparison_path = OUTPUT_DIR / "august_submeter_group_comparison.csv"

comparison.to_csv(comparison_path)

print("\nReports saved:")
print(report_path)
print(comparison_path)

# --------------------------------------------------
# STEP 9: Plot energy and sub-meter readings
# --------------------------------------------------

fig, axes = plt.subplots(
    2, 1, figsize=(15, 10), sharex=True
)

axes[0].plot(
    hourly.index,
    hourly["Energy_kWh"],
    label="Total energy",
    linewidth=1
)

axes[0].axhline(
    threshold_95,
    linestyle="--",
    label=f"95th percentile ({threshold_95:.2f} kWh)"
)

axes[0].axhline(
    threshold_99,
    linestyle=":",
    label=f"99th percentile ({threshold_99:.2f} kWh)"
)

axes[0].set_title(
    "August 2008: Total Hourly Energy Consumption"
)
axes[0].set_ylabel("Energy (kWh)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

for col in submeter_columns:
    axes[1].plot(
        hourly.index,
        hourly[col],
        label=col,
        linewidth=1
    )

axes[1].set_title("Hourly Sub-meter Energy Readings")
axes[1].set_xlabel("Date and Time")
axes[1].set_ylabel("Sub-meter energy (kWh)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()

chart_path = OUTPUT_DIR / "august_submeter_anomaly_validation.png"

plt.savefig(chart_path, dpi=150, bbox_inches="tight")
print(f"Chart saved to: {chart_path}")

plt.show()
