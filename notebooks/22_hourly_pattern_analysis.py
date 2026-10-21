
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# STEP 1: File paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR / "data" /
    "household_power_consumption_cleaned.csv"
)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# STEP 2: Load dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

print("\nDATASET LOADED")
print("=" * 70)
print("Rows:", len(df))
print("Columns:", df.columns.tolist())

# --------------------------------------------------
# STEP 3: Parse datetime
# --------------------------------------------------

if "Datetime" in df.columns:
    # Detect the format from a valid example
    sample = df["Datetime"].dropna().astype(str).iloc[0]

    if len(sample) >= 10 and sample[4] == "-":
        df["Datetime"] = pd.to_datetime(
            df["Datetime"],
            format="mixed",
            errors="coerce"
        )
    else:
        df["Datetime"] = pd.to_datetime(
            df["Datetime"],
            dayfirst=True,
            errors="coerce"
        )

elif "Date" in df.columns and "Time" in df.columns:
    df["Datetime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        dayfirst=True,
        errors="coerce"
    )

else:
    raise ValueError(
        "Datetime column nahi mila. Dataset ke column names check karo."
    )

# --------------------------------------------------
# STEP 4: Validate required column
# --------------------------------------------------

if "Global_active_power" not in df.columns:
    raise ValueError(
        "Global_active_power column dataset mein nahi mila."
    )

df["Global_active_power"] = pd.to_numeric(
    df["Global_active_power"], errors="coerce"
)

df = df.dropna(
    subset=["Datetime", "Global_active_power"]
)

# --------------------------------------------------
# STEP 5: Convert minute readings into hourly energy
# --------------------------------------------------

df = df.sort_values("Datetime").set_index("Datetime")

# Original dataset records are minute-level.
# Global_active_power is in kW.
# Hourly energy (kWh) = sum of minute-level kW / 60.

hourly = df["Global_active_power"].resample("h").agg(
    ["sum", "count"]
)

hourly["Energy_kWh"] = hourly["sum"] / 60

# Use only complete hours containing 60 readings.
hourly = hourly[hourly["count"] == 60].copy()

if hourly.empty:
    raise ValueError(
        "Koi complete hour nahi mila. Dataset frequency check karo."
    )

# --------------------------------------------------
# STEP 6: Create time-based features
# --------------------------------------------------

hourly["Hour"] = hourly.index.hour
hourly["Day"] = hourly.index.day_name()
hourly["Month"] = hourly.index.month
hourly["Weekday_Number"] = hourly.index.dayofweek

hourly["Day_Type"] = hourly["Weekday_Number"].apply(
    lambda x: "Weekend" if x >= 5 else "Weekday"
)

# --------------------------------------------------
# STEP 7: Average consumption by hour of day
# --------------------------------------------------

hourly_pattern = hourly.groupby("Hour")["Energy_kWh"].agg(
    ["mean", "median", "max", "count"]
)

hourly_pattern.columns = [
    "Average_Energy_kWh",
    "Median_Energy_kWh",
    "Maximum_Energy_kWh",
    "Number_of_Hours"
]

print("\nAVERAGE CONSUMPTION BY HOUR OF DAY")
print("=" * 70)
print(hourly_pattern.round(3).to_string())

peak_hour = hourly_pattern["Average_Energy_kWh"].idxmax()
low_hour = hourly_pattern["Average_Energy_kWh"].idxmin()

print("\nHIGHEST AVERAGE CONSUMPTION HOUR")
print(
    f"{peak_hour:02d}:00 - "
    f"{hourly_pattern.loc[peak_hour, 'Average_Energy_kWh']:.3f} kWh"
)

print("\nLOWEST AVERAGE CONSUMPTION HOUR")
print(
    f"{low_hour:02d}:00 - "
    f"{hourly_pattern.loc[low_hour, 'Average_Energy_kWh']:.3f} kWh"
)

# --------------------------------------------------
# STEP 8: Weekday vs weekend by hour
# --------------------------------------------------

day_type_pattern = hourly.groupby(
    ["Day_Type", "Hour"]
)["Energy_kWh"].mean().unstack("Day_Type")

print("\nWEEKDAY VS WEEKEND BY HOUR")
print("=" * 70)
print(day_type_pattern.round(3).to_string())

# --------------------------------------------------
# STEP 9: Average consumption by day of week
# --------------------------------------------------

day_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

daily_pattern = hourly.groupby("Day")["Energy_kWh"].mean()
daily_pattern = daily_pattern.reindex(day_order)

print("\nAVERAGE CONSUMPTION BY DAY OF WEEK")
print("=" * 70)
print(daily_pattern.round(3).to_string())

# --------------------------------------------------
# STEP 10: Save analysis reports
# --------------------------------------------------

hourly_pattern.to_csv(
    OUTPUT_DIR / "hourly_consumption_pattern.csv"
)

day_type_pattern.to_csv(
    OUTPUT_DIR / "weekday_weekend_hourly_pattern.csv"
)

daily_pattern.to_csv(
    OUTPUT_DIR / "day_of_week_consumption_pattern.csv"
)

print("\nCSV REPORTS SAVED IN outputs/")

# --------------------------------------------------
# STEP 11: Plot average hourly consumption
# --------------------------------------------------

plt.figure(figsize=(13, 6))

plt.plot(
    hourly_pattern.index,
    hourly_pattern["Average_Energy_kWh"],
    marker="o",
    linewidth=2,
    label="Average hourly energy"
)

plt.xticks(range(24))
plt.xlabel("Hour of Day")
plt.ylabel("Average Energy (kWh)")
plt.title("Average Electricity Consumption by Hour")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "average_hourly_consumption.png",
    dpi=150
)

plt.show()

# --------------------------------------------------
# STEP 12: Plot weekday vs weekend
# --------------------------------------------------

plt.figure(figsize=(13, 6))

for day_type in day_type_pattern.columns:
    plt.plot(
        day_type_pattern.index,
        day_type_pattern[day_type],
        marker="o",
        linewidth=2,
        label=day_type
    )

plt.xticks(range(24))
plt.xlabel("Hour of Day")
plt.ylabel("Average Energy (kWh)")
plt.title("Hourly Consumption: Weekday vs Weekend")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "weekday_weekend_hourly_pattern.png",
    dpi=150
)

plt.show()

print("\nANALYSIS COMPLETED SUCCESSFULLY!")
