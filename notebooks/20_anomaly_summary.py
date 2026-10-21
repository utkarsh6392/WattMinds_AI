
import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# 1. File paths
# -----------------------------
DATA_PATH = Path("data/household_power_consumption_cleaned.csv")
OUTPUT_PATH = Path("outputs")

OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# -----------------------------
# 2. Load dataset
# -----------------------------
df = pd.read_csv(DATA_PATH)

# Parse timestamp
df["Datetime"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    errors="coerce"
)

df = df.dropna(subset=["Datetime"])

# Convert active power to numeric
df["Global_active_power"] = pd.to_numeric(
    df["Global_active_power"],
    errors="coerce"
)

# -----------------------------
# 3. Create hourly energy
# -----------------------------
df["Energy_kWh"] = df["Global_active_power"] / 60

hourly = (
    df.set_index("Datetime")["Energy_kWh"]
    .resample("h")
    .sum(min_count=60)
    .dropna()
    .reset_index()
)

# Keep August 2008
august = hourly[
    (hourly["Datetime"] >= "2008-08-01") &
    (hourly["Datetime"] < "2008-09-01")
].copy()

# -----------------------------
# 4. Calculate thresholds
# -----------------------------
p95 = august["Energy_kWh"].quantile(0.95)
p99 = august["Energy_kWh"].quantile(0.99)

august["Above_95th"] = august["Energy_kWh"] > p95
august["Above_99th"] = august["Energy_kWh"] > p99

# -----------------------------
# 5. Print summary
# -----------------------------
print("\nAUGUST 2008 ANOMALY SUMMARY")
print("=" * 65)

print(f"Complete hourly records: {len(august)}")
print(f"95th percentile threshold: {p95:.3f} kWh")
print(f"99th percentile threshold: {p99:.3f} kWh")

print(
    "Readings above 95th percentile:",
    int(august["Above_95th"].sum())
)

print(
    "Readings above 99th percentile:",
    int(august["Above_99th"].sum())
)

print("\nTOP 15 HIGHEST HOURLY READINGS")
print("-" * 65)

top_readings = august.nlargest(15, "Energy_kWh")

print(
    top_readings[
        ["Datetime", "Energy_kWh", "Above_95th", "Above_99th"]
    ].to_string(index=False)
)

# -----------------------------
# 6. Daily anomaly summary
# -----------------------------
august["Date"] = august["Datetime"].dt.date

daily = (
    august.groupby("Date")
    .agg(
        Average_Energy_kWh=("Energy_kWh", "mean"),
        Maximum_Energy_kWh=("Energy_kWh", "max"),
        Readings_Above_95th=("Above_95th", "sum"),
        Readings_Above_99th=("Above_99th", "sum")
    )
    .round(3)
)

print("\nDAILY ANOMALY SUMMARY")
print("-" * 65)
print(daily.to_string())

# -----------------------------
# 7. Save reports
# -----------------------------
august.to_csv(
    OUTPUT_PATH / "august_hourly_anomaly_report.csv",
    index=False
)

daily.to_csv(
    OUTPUT_PATH / "august_daily_anomaly_summary.csv"
)

print("\nReports saved:")
print("outputs/august_hourly_anomaly_report.csv")
print("outputs/august_daily_anomaly_summary.csv")
