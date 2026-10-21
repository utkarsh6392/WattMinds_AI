
from pathlib import Path
from datetime import datetime
import warnings

import joblib
import numpy as np
import pandas as pd


# ============================================================
# WATTMinds | ENERGY RECOMMENDATION ENGINE
# Version: 1.0
# Purpose: Forecast, consumption intelligence, recommendations,
#          and estimated energy-saving scenarios.
# ============================================================

warnings.filterwarnings("ignore", category=FutureWarning)


# ------------------------------------------------------------
# STEP 1: PROJECT CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

HOURLY_DATA_PATH = DATA_DIR / "hourly_energy_data.csv"
ML_DATA_PATH = DATA_DIR / "ml_ready_dataset.csv"
MODEL_PATH = MODEL_DIR / "final_energy_prediction_model.joblib"

RECOMMENDATION_PATH = OUTPUT_DIR / "energy_recommendations.csv"
FORECAST_PATH = OUTPUT_DIR / "next_hour_energy_forecast.csv"
SAVINGS_PATH = OUTPUT_DIR / "energy_savings_scenarios.csv"
REPORT_PATH = OUTPUT_DIR / "energy_recommendation_report.txt"

# Example tariff only. Replace with the applicable electricity rate.
TARIFF_PER_KWH = 8.0

# Recommendation configuration
HIGH_USAGE_MULTIPLIER = 1.25
LOW_USAGE_MULTIPLIER = 0.75
UNUSUAL_USAGE_MULTIPLIER = 1.50

SAVING_SCENARIOS = [5, 10, 15]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# STEP 2: VALIDATE FILES
# ------------------------------------------------------------

print("\n" + "=" * 68)
print("WATTMinds | ENERGY RECOMMENDATION ENGINE")
print("=" * 68)

required_files = [
    HOURLY_DATA_PATH,
    ML_DATA_PATH,
    MODEL_PATH
]

for file_path in required_files:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

hourly_data = pd.read_csv(HOURLY_DATA_PATH)
ml_data = pd.read_csv(ML_DATA_PATH)
model = joblib.load(MODEL_PATH)

print("\nAll required files loaded successfully.")


# ------------------------------------------------------------
# STEP 3: VALIDATE AND PREPARE HISTORICAL DATA
# ------------------------------------------------------------

required_hourly_columns = ["Energy_kWh"]

for column in required_hourly_columns:
    if column not in hourly_data.columns:
        raise ValueError(
            f"Missing column in hourly dataset: {column}"
        )

if "Hour" not in hourly_data.columns:
    raise ValueError(
        "The hourly dataset must contain a 'Hour' timestamp column."
    )

hourly_data["Hour"] = pd.to_datetime(
    hourly_data["Hour"],
    errors="coerce"
)

hourly_data["Energy_kWh"] = pd.to_numeric(
    hourly_data["Energy_kWh"],
    errors="coerce"
)

hourly_data = hourly_data.dropna(
    subset=["Hour", "Energy_kWh"]
)

hourly_data = hourly_data.sort_values("Hour")
hourly_data = hourly_data.drop_duplicates(
    subset=["Hour"],
    keep="last"
).reset_index(drop=True)

if hourly_data.empty:
    raise ValueError("No valid hourly energy records were found.")

if (hourly_data["Energy_kWh"] < 0).any():
    raise ValueError(
        "Negative energy values found. Check the dataset before proceeding."
    )

hourly_data["Hour_of_Day"] = hourly_data["Hour"].dt.hour
hourly_data["Day_of_Week"] = hourly_data["Hour"].dt.dayofweek
hourly_data["Month"] = hourly_data["Hour"].dt.month

print("Valid hourly records:", len(hourly_data))
print("Historical start:", hourly_data["Hour"].min())
print("Historical end:", hourly_data["Hour"].max())


# ------------------------------------------------------------
# STEP 4: BUILD HISTORICAL CONSUMPTION BASELINES
# ------------------------------------------------------------

# Overall average energy consumption per recorded hour.
overall_mean = hourly_data["Energy_kWh"].mean()
overall_median = hourly_data["Energy_kWh"].median()

# Compare an hour with historical observations for the same hour
# of the day. This accounts for normal daily consumption patterns.
hourly_baseline = (
    hourly_data.groupby("Hour_of_Day")["Energy_kWh"]
    .mean()
    .to_dict()
)

hourly_data["Historical_Hour_Baseline_kWh"] = (
    hourly_data["Hour_of_Day"]
    .map(hourly_baseline)
)

hourly_data["Deviation_Percent"] = np.where(
    hourly_data["Historical_Hour_Baseline_kWh"] > 0,
    (
        (
            hourly_data["Energy_kWh"]
            - hourly_data["Historical_Hour_Baseline_kWh"]
        )
        / hourly_data["Historical_Hour_Baseline_kWh"]
    ) * 100,
    np.nan
)

print(f"\nOverall mean consumption: {overall_mean:.4f} kWh/hour")
print(f"Overall median consumption: {overall_median:.4f} kWh/hour")


# ------------------------------------------------------------
# STEP 5: GENERATE HISTORICAL RECOMMENDATIONS
# ------------------------------------------------------------

def classify_consumption(actual, baseline):
    """Classify consumption relative to the hour-of-day baseline."""

    if pd.isna(actual) or pd.isna(baseline) or baseline <= 0:
        return "Insufficient baseline"

    if actual >= baseline * UNUSUAL_USAGE_MULTIPLIER:
        return "Unusually high"

    if actual >= baseline * HIGH_USAGE_MULTIPLIER:
        return "High"

    if actual <= baseline * LOW_USAGE_MULTIPLIER:
        return "Low"

    return "Normal"


def create_recommendation(row):
    """Create an actionable recommendation based on observed usage."""

    level = row["Consumption_Level"]
    hour = int(row["Hour_of_Day"])

    if level == "Unusually high":
        return (
            "Review the appliances and activities operating during this hour. "
            "Compare similar days before deciding whether usage is abnormal."
        )

    if level == "High":
        if 17 <= hour <= 22:
            return (
                "Review evening peak usage. If practical, shift flexible "
                "activities to lower-consumption hours."
            )

        return (
            "Check whether high-consumption appliances can be used more "
            "efficiently or scheduled for another suitable hour."
        )

    if level == "Low":
        return (
            "Consumption is below the historical baseline for this hour. "
            "Use this period as a comparison point for similar days."
        )

    if level == "Normal":
        return (
            "Consumption is within the expected historical range. "
            "Continue monitoring recurring patterns."
        )

    return (
        "Collect more comparable historical observations before classifying "
        "this hour."
    )


hourly_data["Consumption_Level"] = hourly_data.apply(
    lambda row: classify_consumption(
        row["Energy_kWh"],
        row["Historical_Hour_Baseline_kWh"]
    ),
    axis=1
)

hourly_data["Recommendation"] = hourly_data.apply(
    create_recommendation,
    axis=1
)

hourly_data["Estimated_Cost_Rs"] = (
    hourly_data["Energy_kWh"] * TARIFF_PER_KWH
)

recommendation_columns = [
    "Hour",
    "Energy_kWh",
    "Historical_Hour_Baseline_kWh",
    "Deviation_Percent",
    "Consumption_Level",
    "Estimated_Cost_Rs",
    "Recommendation"
]

recommendations_df = hourly_data[recommendation_columns].copy()

recommendations_df.to_csv(
    RECOMMENDATION_PATH,
    index=False
)

print("\nHistorical recommendation file saved.")
print("Usage classifications:")
print(
    hourly_data["Consumption_Level"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# STEP 6: PREDICT ENERGY FOR THE NEXT TARGET HOUR
# ------------------------------------------------------------

# These must match the features used during model training.
feature_columns = [
    "Hour_of_Day",
    "Day_of_Week",
    "Day_of_Month",
    "Month",
    "Is_Weekend",
    "Lag_1h",
    "Lag_2h",
    "Lag_24h",
    "Rolling_Mean_3h",
    "Rolling_Mean_24h"
]

missing_features = [
    column for column in feature_columns
    if column not in ml_data.columns
]

if missing_features:
    raise ValueError(
        "Missing ML feature columns: "
        + ", ".join(missing_features)
    )

if ml_data.empty:
    raise ValueError("The ML-ready dataset is empty.")

# Use the most recent feature row created by the preparation pipeline.
latest_feature_row = ml_data.iloc[[-1]][feature_columns].copy()

if latest_feature_row.isna().any().any():
    raise ValueError(
        "The latest prediction row contains missing feature values."
    )

predicted_energy = float(model.predict(latest_feature_row)[0])

# Energy consumption cannot be negative.
predicted_energy = max(0.0, predicted_energy)

latest_observed_hour = hourly_data["Hour"].max()

# Forecast is for the hour following the latest observed timestamp.
forecast_hour = latest_observed_hour + pd.Timedelta(hours=1)

forecast_hour_of_day = forecast_hour.hour

forecast_baseline = hourly_baseline.get(
    forecast_hour_of_day,
    overall_mean
)

forecast_deviation = (
    (predicted_energy - forecast_baseline) / forecast_baseline * 100
    if forecast_baseline > 0
    else np.nan
)

forecast_level = classify_consumption(
    predicted_energy,
    forecast_baseline
)

forecast_cost = predicted_energy * TARIFF_PER_KWH

forecast_df = pd.DataFrame([{
    "Forecast_Hour": forecast_hour,
    "Latest_Observed_Hour": latest_observed_hour,
    "Predicted_Energy_kWh": predicted_energy,
    "Historical_Hour_Baseline_kWh": forecast_baseline,
    "Deviation_Percent": forecast_deviation,
    "Consumption_Level": forecast_level,
    "Estimated_Cost_Rs": forecast_cost,
    "Tariff_Rs_per_kWh": TARIFF_PER_KWH
}])

forecast_df.to_csv(FORECAST_PATH, index=False)

print("\n" + "-" * 68)
print("NEXT-HOUR ENERGY FORECAST")
print("-" * 68)
print("Latest observed hour:", latest_observed_hour)
print("Forecast hour:", forecast_hour)
print(f"Predicted energy: {predicted_energy:.4f} kWh")
print(f"Historical hour baseline: {forecast_baseline:.4f} kWh")
print(f"Estimated cost: Rs. {forecast_cost:.2f}")
print("Forecast classification:", forecast_level)


# ------------------------------------------------------------
# STEP 7: CREATE FORECAST-SPECIFIC RECOMMENDATIONS
# ------------------------------------------------------------

if forecast_level == "Unusually high":
    forecast_recommendation = (
        "Forecast is substantially above the historical baseline for this "
        "hour. Review expected appliance usage and check for avoidable loads."
    )

elif forecast_level == "High":
    forecast_recommendation = (
        "Forecast is above the historical baseline. Consider shifting "
        "flexible electricity use if it is practical and safe."
    )

elif forecast_level == "Low":
    forecast_recommendation = (
        "Forecast is below the historical baseline for this hour. "
        "Continue monitoring to confirm whether this is a recurring pattern."
    )

else:
    forecast_recommendation = (
        "Forecast does not indicate unusually high consumption relative "
        "to the hour-specific historical baseline."
    )

forecast_df["Recommendation"] = forecast_recommendation
forecast_df.to_csv(FORECAST_PATH, index=False)

print("\nForecast recommendation:")
print(forecast_recommendation)


# ------------------------------------------------------------
# STEP 8: WHAT-IF ENERGY SAVINGS SIMULATOR
# ------------------------------------------------------------

# Use the most recent 24 recorded hourly observations.
# If the dataset contains missing hours, these are the most recent
# 24 available records, not necessarily 24 consecutive clock hours.

recent_records = hourly_data.tail(24).copy()

recent_energy = recent_records["Energy_kWh"].sum()
recent_cost = recent_energy * TARIFF_PER_KWH

savings_results = []

for reduction_percent in SAVING_SCENARIOS:

    reduction_fraction = reduction_percent / 100

    estimated_energy_saved = recent_energy * reduction_fraction
    estimated_energy_after = recent_energy - estimated_energy_saved
    estimated_cost_saved = estimated_energy_saved * TARIFF_PER_KWH
    estimated_cost_after = estimated_energy_after * TARIFF_PER_KWH

    savings_results.append({
        "Scenario": f"{reduction_percent}% reduction",
        "Reduction_Percent": reduction_percent,
        "Baseline_Energy_kWh": recent_energy,
        "Estimated_Energy_Saved_kWh": estimated_energy_saved,
        "Estimated_Energy_After_Reduction_kWh": estimated_energy_after,
        "Baseline_Cost_Rs": recent_cost,
        "Estimated_Cost_Saved_Rs": estimated_cost_saved,
        "Estimated_Cost_After_Rs": estimated_cost_after,
        "Tariff_Rs_per_kWh": TARIFF_PER_KWH
    })

savings_df = pd.DataFrame(savings_results)

savings_df.to_csv(SAVINGS_PATH, index=False)

print("\n" + "-" * 68)
print("WHAT-IF SAVINGS SCENARIOS")
print("-" * 68)
print(f"Recent 24-record energy total: {recent_energy:.4f} kWh")
print(f"Estimated baseline cost: Rs. {recent_cost:.2f}")
print(savings_df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


# ------------------------------------------------------------
# STEP 9: GENERATE PREMIUM TEXT REPORT
# ------------------------------------------------------------

latest_record = hourly_data.iloc[-1]

high_count = int(
    hourly_data["Consumption_Level"].isin(
        ["High", "Unusually high"]
    ).sum()
)

unusual_count = int(
    (hourly_data["Consumption_Level"] == "Unusually high").sum()
)

report_lines = [
    "=" * 72,
    "WATTMinds | ENERGY INTELLIGENCE AND RECOMMENDATION REPORT",
    "=" * 72,
    "",
    "1. DATASET OVERVIEW",
    "-" * 72,
    f"Valid hourly records: {len(hourly_data):,}",
    f"Historical start: {hourly_data['Hour'].min()}",
    f"Historical end: {hourly_data['Hour'].max()}",
    f"Overall mean energy: {overall_mean:.4f} kWh/hour",
    f"Overall median energy: {overall_median:.4f} kWh/hour",
    "",
    "2. LATEST OBSERVED CONSUMPTION",
    "-" * 72,
    f"Timestamp: {latest_record['Hour']}",
    f"Observed energy: {latest_record['Energy_kWh']:.4f} kWh",
    f"Historical baseline for this hour: "
    f"{latest_record['Historical_Hour_Baseline_kWh']:.4f} kWh",
    f"Classification: {latest_record['Consumption_Level']}",
    "",
    "3. NEXT-HOUR FORECAST",
    "-" * 72,
    f"Forecast timestamp: {forecast_hour}",
    f"Predicted energy: {predicted_energy:.4f} kWh",
    f"Historical hour baseline: {forecast_baseline:.4f} kWh",
    f"Classification: {forecast_level}",
    f"Estimated cost: Rs. {forecast_cost:.2f}",
    f"Recommendation: {forecast_recommendation}",
    "",
    "4. HISTORICAL CONSUMPTION INTELLIGENCE",
    "-" * 72,
    f"High or unusually high records: {high_count:,}",
    f"Unusually high records: {unusual_count:,}",
    "",
    "5. WHAT-IF SAVINGS SCENARIOS",
    "-" * 72,
    "Reference period: most recent 24 available hourly records",
    f"Baseline energy: {recent_energy:.4f} kWh",
    f"Illustrative tariff: Rs. {TARIFF_PER_KWH:.2f}/kWh",
    savings_df.to_string(index=False),
    "",
    "6. INTERPRETATION AND LIMITATIONS",
    "-" * 72,
    "- Forecasts are estimates, not guaranteed future consumption.",
    "- The model does not identify individual appliances.",
    "- High usage is compared with the historical average for the same hour.",
    "- Historical differences do not by themselves prove abnormal behaviour.",
    "- Savings scenarios are mathematical what-if estimates, not measured savings.",
    "- Actual electricity cost depends on the applicable tariff and billing rules.",
    "- This system provides decision support; it does not control appliances.",
    "",
    "Generated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "=" * 72
]

with open(REPORT_PATH, "w", encoding="utf-8") as file:
    file.write("\n".join(report_lines))


# ------------------------------------------------------------
# STEP 10: FINAL SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 68)
print("ENERGY RECOMMENDATION ENGINE COMPLETED")
print("=" * 68)

print("\nFiles generated:")
print("1.", RECOMMENDATION_PATH)
print("2.", FORECAST_PATH)
print("3.", SAVINGS_PATH)
print("4.", REPORT_PATH)

print("\nAll outputs are saved inside the outputs folder.")
print("No original dataset files were modified.")
