
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# STEP 1: PATHS AND SETTINGS
# ==========================================

DATA_PATH = Path("data/household_power_consumption_cleaned.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# STEP 2: LOAD DATA
# ==========================================

df = pd.read_csv(DATA_PATH)

# Convert DateTime column
# Change "DateTime" below if your CSV uses another column name.
if "DateTime" in df.columns:
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
elif {"Date", "Time"}.issubset(df.columns):
    df["DateTime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        errors="coerce",
        dayfirst=True
    )
else:
    raise ValueError(
        "DateTime column nahi mili. CSV ke date/time column names check karo."
    )

df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
df = df.set_index("DateTime")

# Required energy columns
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
    raise ValueError(f"Missing columns: {missing_columns}")

for col in required_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ==========================================
# STEP 3: CREATE HOURLY ENERGY DATA
# ==========================================

# Global_active_power is in kW.
# For minute-level readings:
# Hourly energy (kWh) = sum of minute-level kW readings / 60

hourly = df[required_columns].resample("h").agg({
    "Global_active_power": "sum",
    "Sub_metering_1": "sum",
    "Sub_metering_2": "sum",
    "Sub_metering_3": "sum"
})

# Count valid minute readings in each hour
hourly["Available_Minutes"] = (
    df["Global_active_power"].resample("h").count()
)

hourly["Energy_kWh"] = hourly["Global_active_power"] / 60

# Sub-meter readings are in Wh per minute.
hourly["Sub_metering_1_kWh"] = hourly["Sub_metering_1"] / 1000
hourly["Sub_metering_2_kWh"] = hourly["Sub_metering_2"] / 1000
hourly["Sub_metering_3_kWh"] = hourly["Sub_metering_3"] / 1000

# Keep only hours having all 60 minute readings
hourly["Complete_Hour"] = hourly["Available_Minutes"] == 60

# Create month and date information
hourly["Year_Month"] = hourly.index.to_period("M").astype(str)
hourly["Date"] = hourly.index.date

# ==========================================
# STEP 4: COMPARE JULY, AUGUST AND SEPTEMBER
# ==========================================

months = ["2008-07", "2008-08", "2008-09"]

comparison_data = hourly[
    hourly["Year_Month"].isin(months)
].copy()

monthly_report = comparison_data.groupby("Year_Month").agg(
    Available_Hours=("Energy_kWh", "count"),
    Complete_Hours=("Complete_Hour", "sum"),
    Average_Energy_kWh=("Energy_kWh", "mean"),
    Median_Energy_kWh=("Energy_kWh", "median"),
    Maximum_Energy_kWh=("Energy_kWh", "max"),
    Total_Energy_kWh=("Energy_kWh", "sum"),
    Average_Global_Active_Power=("Global_active_power", "mean"),
    Average_Submeter_1=("Sub_metering_1_kWh", "mean"),
    Average_Submeter_2=("Sub_metering_2_kWh", "mean"),
    Average_Submeter_3=("Sub_metering_3_kWh", "mean")
).round(3)

print("\nMONTHLY COMPARISON: JULY, AUGUST AND SEPTEMBER")
print("=" * 85)
print(monthly_report.to_string())

monthly_report.to_csv(
    OUTPUT_DIR / "august_monthly_comparison.csv"
)

# ==========================================
# STEP 5: FIND UNUSUAL AUGUST HOURS
# ==========================================

august = hourly[
    hourly.index.to_period("M") == "2008-08"
].copy()

# Use complete hours for a fairer comparison
august_complete = august[august["Complete_Hour"]].copy()

if august_complete.empty:
    raise ValueError("August 2008 mein complete hourly readings nahi mili.")

# Calculate percentile thresholds from August itself
p95 = august_complete["Energy_kWh"].quantile(0.95)
p99 = august_complete["Energy_kWh"].quantile(0.99)
median = august_complete["Energy_kWh"].median()

# High readings are flagged for investigation, not automatically deleted
august_complete["High_Reading_Flag"] = (
    august_complete["Energy_kWh"] > p95
)

august_complete["Extreme_Reading_Flag"] = (
    august_complete["Energy_kWh"] > p99
)

high_readings = august_complete[
    august_complete["High_Reading_Flag"]
].sort_values("Energy_kWh", ascending=False)

print("\nAUGUST CONSUMPTION THRESHOLDS")
print("=" * 50)
print(f"Median energy: {median:.3f} kWh")
print(f"95th percentile: {p95:.3f} kWh")
print(f"99th percentile: {p99:.3f} kWh")
print(f"Hours above 95th percentile: {len(high_readings)}")

print("\nTOP 15 HIGH-CONSUMPTION HOURS")
print("=" * 85)

display_columns = [
    "Energy_kWh",
    "Global_active_power",
    "Sub_metering_1_kWh",
    "Sub_metering_2_kWh",
    "Sub_metering_3_kWh",
    "Available_Minutes",
    "High_Reading_Flag",
    "Extreme_Reading_Flag"
]

print(
    high_readings[display_columns]
    .sort_values("Energy_kWh", ascending=False)
    .head(15)
    .round(3)
    .to_string()
)

high_readings.to_csv(
    OUTPUT_DIR / "august_high_consumption_hours.csv"
)

# ==========================================
# STEP 6: FIND SUDDEN CHANGES
# ==========================================

august_complete["Previous_Hour_Energy_kWh"] = (
    august_complete["Energy_kWh"].shift(1)
)

august_complete["Change_kWh"] = (
    august_complete["Energy_kWh"]
    - august_complete["Previous_Hour_Energy_kWh"]
)

# A large change is a candidate for investigation.
# It is not proof of a faulty reading.
august_complete["Absolute_Change_kWh"] = (
    august_complete["Change_kWh"].abs()
)

change_threshold = august_complete[
    "Absolute_Change_kWh"
].quantile(0.95)

sudden_changes = august_complete[
    august_complete["Absolute_Change_kWh"] > change_threshold
].copy()

print("\nSUDDEN HOURLY CHANGES")
print("=" * 70)
print(f"95th percentile of absolute hourly changes: {change_threshold:.3f} kWh")

print(
    sudden_changes[
        [
            "Energy_kWh",
            "Previous_Hour_Energy_kWh",
            "Change_kWh",
            "Absolute_Change_kWh"
        ]
    ]
    .sort_values("Absolute_Change_kWh", ascending=False)
    .head(15)
    .round(3)
    .to_string()
)

sudden_changes.to_csv(
    OUTPUT_DIR / "august_sudden_changes.csv"
)

# ==========================================
# STEP 7: DAILY ENERGY AND DATA COVERAGE
# ==========================================

august["Date"] = august.index.date

daily_report = august.groupby("Date").agg(
    Available_Hours=("Energy_kWh", "count"),
    Complete_Hours=("Complete_Hour", "sum"),
    Daily_Energy_kWh=("Energy_kWh", "sum"),
    Average_Hourly_Energy_kWh=("Energy_kWh", "mean"),
    Maximum_Hourly_Energy_kWh=("Energy_kWh", "max")
).round(3)

# Daily total can be misleading when hours are missing.
# Keep coverage visible so incomplete days can be investigated.
daily_report["Coverage_Percent"] = (
    daily_report["Available_Hours"] / 24 * 100
).round(2)

print("\nAUGUST DAILY REPORT")
print("=" * 85)
print(daily_report.to_string())

daily_report.to_csv(
    OUTPUT_DIR / "august_daily_anomaly_report.csv"
)

# ==========================================
# STEP 8: PLOT HOURLY ENERGY
# ==========================================

plt.figure(figsize=(15, 6))

plt.plot(
    august_complete.index,
    august_complete["Energy_kWh"],
    linewidth=1,
    label="Hourly energy"
)

plt.axhline(
    p95,
    linestyle="--",
    label=f"95th percentile ({p95:.2f} kWh)"
)

plt.axhline(
    p99,
    linestyle=":",
    label=f"99th percentile ({p99:.2f} kWh)"
)

plt.title("August 2008: Hourly Energy and High-Reading Thresholds")
plt.xlabel("Date and Time")
plt.ylabel("Energy Consumption (kWh)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "august_hourly_anomaly_check.png",
    dpi=150
)

plt.show()

# ==========================================
# STEP 9: PLOT DAILY ENERGY
# ==========================================

plt.figure(figsize=(14, 5))

plt.plot(
    daily_report.index.astype(str),
    daily_report["Daily_Energy_kWh"],
    marker="o"
)

plt.title("August 2008: Daily Recorded Energy Consumption")
plt.xlabel("Date")
plt.ylabel("Recorded Energy (kWh)")
plt.xticks(rotation=60)
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "august_daily_energy_check.png",
    dpi=150
)

plt.show()

# ==========================================
# STEP 10: FINAL SUMMARY
# ==========================================

print("\nINVESTIGATION COMPLETE")
print("=" * 60)
print(f"August hourly records: {len(august)}")
print(f"Complete hours: {len(august_complete)}")
print(f"High readings flagged: {len(high_readings)}")
print(f"Sudden changes flagged: {len(sudden_changes)}")

print("\nFiles saved in outputs/:")
print("- august_monthly_comparison.csv")
print("- august_high_consumption_hours.csv")
print("- august_sudden_changes.csv")
print("- august_daily_anomaly_report.csv")
print("- august_hourly_anomaly_check.png")
print("- august_daily_energy_check.png")

print("\nNote: Flags identify readings to investigate.")
print("They do not automatically mean the readings are incorrect.")
