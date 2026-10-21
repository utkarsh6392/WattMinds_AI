
# ============================================================
# WattMinds
# Premium ML Model Evaluation & Visualization
# ============================================================

import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

X_TEST_FILE = DATA_DIR / "X_test.csv"
Y_TEST_FILE = DATA_DIR / "y_test.csv"
ML_DATA_FILE = DATA_DIR / "ml_ready_dataset.csv"

MODEL_FILE = MODEL_DIR / "random_forest_model.joblib"
COMPARISON_FILE = OUTPUT_DIR / "model_comparison.csv"

PREDICTIONS_FILE = OUTPUT_DIR / "test_predictions.csv"
METRICS_FILE = OUTPUT_DIR / "detailed_evaluation_metrics.csv"
HOURLY_METRICS_FILE = OUTPUT_DIR / "hourly_evaluation_metrics.csv"
REPORT_FILE = OUTPUT_DIR / "premium_model_evaluation_report.txt"

PLOT_FILES = {
    "dashboard": OUTPUT_DIR / "evaluation_dashboard.png",
    "actual_predicted": OUTPUT_DIR / "actual_vs_predicted.png",
    "residuals": OUTPUT_DIR / "residual_analysis.png",
    "error_distribution": OUTPUT_DIR / "error_distribution.png",
    "hourly_mae": OUTPUT_DIR / "hourly_mae.png",
    "feature_importance": OUTPUT_DIR / "feature_importance.png"
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Consistent, professional chart styling
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.20,
    "figure.facecolor": "white",
    "axes.facecolor": "white"
})


# ============================================================
# 2. LOAD AND VALIDATE INPUT FILES
# ============================================================

required_files = [
    X_TEST_FILE,
    Y_TEST_FILE,
    ML_DATA_FILE,
    MODEL_FILE
]

for file_path in required_files:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

X_test = pd.read_csv(X_TEST_FILE)
y_test = pd.read_csv(Y_TEST_FILE).squeeze("columns")

ml_data = pd.read_csv(
    ML_DATA_FILE,
    parse_dates=["Hour"]
)

model = joblib.load(MODEL_FILE)

target_column = "Target_Next_Hour_kWh"

if target_column not in ml_data.columns:
    raise ValueError(
        f"Target column not found: {target_column}"
    )

if len(X_test) != len(y_test):
    raise ValueError(
        "X_test and y_test have different row counts."
    )

if X_test.columns.tolist() != list(model.feature_names_in_):
    raise ValueError(
        "Test feature columns or their order do not match the model."
    )

if not np.isfinite(X_test.to_numpy(dtype=float)).all():
    raise ValueError("X_test contains missing or infinite values.")

if not np.isfinite(y_test.to_numpy(dtype=float)).all():
    raise ValueError("y_test contains missing or infinite values.")

if ml_data["Hour"].duplicated().any():
    raise ValueError("Duplicate timestamps found in ML dataset.")

if not ml_data["Hour"].is_monotonic_increasing:
    raise ValueError("ML dataset is not in chronological order.")

# Recover the exact timestamps belonging to the test rows.
split_index = int(len(ml_data) * 0.80)

test_data = ml_data.iloc[split_index:].reset_index(drop=True)

if len(test_data) != len(X_test):
    raise ValueError(
        "Test timestamps cannot be aligned with X_test."
    )

if not np.allclose(
    test_data[target_column].to_numpy(),
    y_test.to_numpy(),
    rtol=1e-9,
    atol=1e-9
):
    raise ValueError(
        "Test target values do not match the chronological ML dataset."
    )

test_timestamps = test_data["Hour"]

print("=" * 60)
print("WATTMinds | PREMIUM MODEL EVALUATION")
print("=" * 60)

print("\nInput validation successful.")
print("Test samples:", len(X_test))
print("Input features:", X_test.shape[1])
print("Test period:", test_timestamps.min(), "to", test_timestamps.max())


# ============================================================
# 3. GENERATE PREDICTIONS
# ============================================================

y_pred = model.predict(X_test)

if not np.isfinite(y_pred).all():
    raise ValueError("Model generated invalid predictions.")

actual = y_test.to_numpy(dtype=float)

# Energy consumption cannot be negative.
# Preserve raw predictions for honest evaluation.
# Clipped predictions are not used for the reported metrics.

residuals = actual - y_pred
absolute_errors = np.abs(residuals)


# ============================================================
# 4. CALCULATE REGRESSION METRICS
# ============================================================

mae = mean_absolute_error(actual, y_pred)
rmse = np.sqrt(mean_squared_error(actual, y_pred))
r2 = r2_score(actual, y_pred)

mean_actual = float(np.mean(actual))
mean_prediction = float(np.mean(y_pred))

mean_error = float(np.mean(residuals))
mean_absolute_error_value = float(np.mean(absolute_errors))

# WAPE is useful for summarizing absolute errors relative
# to total actual consumption.
total_actual = float(np.sum(np.abs(actual)))

wape = (
    float(np.sum(absolute_errors) / total_actual * 100)
    if total_actual > 0
    else np.nan
)

metrics = pd.DataFrame([
    {"Metric": "MAE_kWh", "Value": mae},
    {"Metric": "RMSE_kWh", "Value": rmse},
    {"Metric": "R2_Score", "Value": r2},
    {"Metric": "Mean_Residual_kWh", "Value": mean_error},
    {"Metric": "Mean_Actual_kWh", "Value": mean_actual},
    {"Metric": "Mean_Predicted_kWh", "Value": mean_prediction},
    {"Metric": "WAPE_Percent", "Value": wape}
])

metrics.to_csv(METRICS_FILE, index=False)


# ============================================================
# 5. BASELINE COMPARISON
# ============================================================

baseline_mae = np.nan
baseline_rmse = np.nan
baseline_r2 = np.nan
mae_improvement = np.nan

if COMPARISON_FILE.exists():
    comparison = pd.read_csv(COMPARISON_FILE)

    baseline_rows = comparison[
        comparison["Model"] == "DummyRegressor"
    ]

    if not baseline_rows.empty:
        baseline_mae = float(
            baseline_rows.iloc[0]["MAE_kWh"]
        )

        baseline_rmse = float(
            baseline_rows.iloc[0]["RMSE_kWh"]
        )

        baseline_r2 = float(
            baseline_rows.iloc[0]["R2_Score"]
        )

        if baseline_mae > 0:
            mae_improvement = (
                (baseline_mae - mae) / baseline_mae * 100
            )


# ============================================================
# 6. BUILD PREDICTION RESULTS
# ============================================================

results = pd.DataFrame({
    "Hour": test_timestamps,
    "Actual_Energy_kWh": actual,
    "Predicted_Energy_kWh": y_pred,
    "Residual_kWh": residuals,
    "Absolute_Error_kWh": absolute_errors
})

results["Percentage_Error"] = np.where(
    results["Actual_Energy_kWh"] != 0,
    results["Absolute_Error_kWh"]
    / results["Actual_Energy_kWh"] * 100,
    np.nan
)

results["Hour_of_Day"] = results["Hour"].dt.hour
results["Day_of_Week"] = results["Hour"].dt.dayofweek

results.to_csv(PREDICTIONS_FILE, index=False)


# ============================================================
# 7. HOURLY PERFORMANCE ANALYSIS
# ============================================================

hourly_metrics = (
    results.groupby("Hour_of_Day")
    .agg(
        Sample_Count=("Absolute_Error_kWh", "size"),
        MAE_kWh=("Absolute_Error_kWh", "mean"),
        RMSE_kWh=(
            "Residual_kWh",
            lambda values: np.sqrt(np.mean(values ** 2))
        ),
        Mean_Actual_kWh=("Actual_Energy_kWh", "mean"),
        Mean_Predicted_kWh=("Predicted_Energy_kWh", "mean")
    )
    .reset_index()
)

hourly_metrics.to_csv(HOURLY_METRICS_FILE, index=False)


# ============================================================
# 8. FEATURE IMPORTANCE
# ============================================================

feature_importance = None

try:
    # The saved model is a pipeline containing a Random Forest.
    forest = model.named_steps["model"]

    feature_importance = pd.DataFrame({
        "Feature": X_test.columns,
        "Importance": forest.feature_importances_
    }).sort_values(
        "Importance",
        ascending=False
    )

    feature_importance.to_csv(
        OUTPUT_DIR / "feature_importance.csv",
        index=False
    )

except (AttributeError, KeyError) as error:
    warnings.warn(
        f"Feature importance unavailable: {error}"
    )


# ============================================================
# 9. VISUALIZATION 1: ACTUAL VS PREDICTED
# ============================================================

fig, ax = plt.subplots(figsize=(9, 7))

ax.scatter(
    actual,
    y_pred,
    alpha=0.35,
    s=20,
    edgecolors="none"
)

plot_max = max(float(actual.max()), float(y_pred.max()))

ax.plot(
    [0, plot_max],
    [0, plot_max],
    linestyle="--",
    linewidth=2,
    label="Perfect prediction"
)

ax.set_xlabel("Actual Energy Consumption (kWh)")
ax.set_ylabel("Predicted Energy Consumption (kWh)")
ax.set_title("Actual vs Predicted Energy Consumption")

ax.text(
    0.04,
    0.96,
    f"MAE: {mae:.3f} kWh\nRMSE: {rmse:.3f} kWh\nR²: {r2:.3f}",
    transform=ax.transAxes,
    va="top",
    bbox={"boxstyle": "round", "alpha": 0.12}
)

ax.legend()
fig.tight_layout()
fig.savefig(PLOT_FILES["actual_predicted"], bbox_inches="tight")
plt.close(fig)


# ============================================================
# 10. VISUALIZATION 2: RESIDUAL ANALYSIS
# ============================================================

fig, ax = plt.subplots(figsize=(10, 6))

ax.scatter(
    y_pred,
    residuals,
    alpha=0.35,
    s=20,
    edgecolors="none"
)

ax.axhline(
    0,
    linestyle="--",
    linewidth=2,
    label="Zero error"
)

ax.set_xlabel("Predicted Energy (kWh)")
ax.set_ylabel("Residual: Actual - Predicted (kWh)")
ax.set_title("Residual Analysis")

ax.legend()
fig.tight_layout()
fig.savefig(PLOT_FILES["residuals"], bbox_inches="tight")
plt.close(fig)


# ============================================================
# 11. VISUALIZATION 3: ERROR DISTRIBUTION
# ============================================================

fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(
    residuals,
    bins=40,
    edgecolor="white",
    alpha=0.85
)

ax.axvline(
    0,
    linestyle="--",
    linewidth=2,
    label="Zero error"
)

ax.axvline(
    mean_error,
    linestyle=":",
    linewidth=2,
    label=f"Mean residual: {mean_error:.3f} kWh"
)

ax.set_xlabel("Residual (kWh)")
ax.set_ylabel("Number of Predictions")
ax.set_title("Distribution of Prediction Errors")

ax.legend()
fig.tight_layout()
fig.savefig(PLOT_FILES["error_distribution"], bbox_inches="tight")
plt.close(fig)


# ============================================================
# 12. VISUALIZATION 4: HOURLY MAE
# ============================================================

fig, ax = plt.subplots(figsize=(11, 6))

ax.bar(
    hourly_metrics["Hour_of_Day"],
    hourly_metrics["MAE_kWh"]
)

ax.set_xticks(range(24))
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Mean Absolute Error (kWh)")
ax.set_title("Model Prediction Error by Hour of Day")

fig.tight_layout()
fig.savefig(PLOT_FILES["hourly_mae"], bbox_inches="tight")
plt.close(fig)


# ============================================================
# 13. VISUALIZATION 5: FEATURE IMPORTANCE
# ============================================================

if feature_importance is not None:
    top_features = feature_importance.head(10).sort_values(
        "Importance",
        ascending=True
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        top_features["Feature"],
        top_features["Importance"]
    )

    ax.set_xlabel("Feature Importance")
    ax.set_ylabel("Input Feature")
    ax.set_title("Random Forest: Top Feature Importance")

    fig.tight_layout()
    fig.savefig(
        PLOT_FILES["feature_importance"],
        bbox_inches="tight"
    )
    plt.close(fig)


# ============================================================
# 14. VISUALIZATION 6: PREMIUM EVALUATION DASHBOARD
# ============================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 11))

# Panel A: Actual vs predicted
axes[0, 0].scatter(
    actual,
    y_pred,
    alpha=0.30,
    s=15,
    edgecolors="none"
)

axes[0, 0].plot(
    [0, plot_max],
    [0, plot_max],
    linestyle="--",
    linewidth=2
)

axes[0, 0].set_title("Actual vs Predicted")
axes[0, 0].set_xlabel("Actual (kWh)")
axes[0, 0].set_ylabel("Predicted (kWh)")

# Panel B: Residuals
axes[0, 1].scatter(
    y_pred,
    residuals,
    alpha=0.30,
    s=15,
    edgecolors="none"
)

axes[0, 1].axhline(0, linestyle="--", linewidth=2)
axes[0, 1].set_title("Residual Analysis")
axes[0, 1].set_xlabel("Predicted (kWh)")
axes[0, 1].set_ylabel("Residual (kWh)")

# Panel C: Error distribution
axes[1, 0].hist(
    residuals,
    bins=35,
    edgecolor="white"
)

axes[1, 0].axvline(0, linestyle="--", linewidth=2)
axes[1, 0].set_title("Prediction Error Distribution")
axes[1, 0].set_xlabel("Residual (kWh)")
axes[1, 0].set_ylabel("Frequency")

# Panel D: Hourly MAE
axes[1, 1].bar(
    hourly_metrics["Hour_of_Day"],
    hourly_metrics["MAE_kWh"]
)

axes[1, 1].set_xticks(range(0, 24, 2))
axes[1, 1].set_title("Hourly MAE")
axes[1, 1].set_xlabel("Hour of Day")
axes[1, 1].set_ylabel("MAE (kWh)")

fig.suptitle(
    "WattMinds | Energy Prediction Evaluation Dashboard",
    fontsize=17,
    fontweight="bold"
)

fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(PLOT_FILES["dashboard"], bbox_inches="tight")
plt.close(fig)


# ============================================================
# 15. GENERATE PROFESSIONAL EVALUATION REPORT
# ============================================================

best_hour = hourly_metrics.loc[
    hourly_metrics["MAE_kWh"].idxmin()
]

worst_hour = hourly_metrics.loc[
    hourly_metrics["MAE_kWh"].idxmax()
]

feature_summary = (
    feature_importance.head(10).to_string(index=False)
    if feature_importance is not None
    else "Feature importance unavailable."
)

baseline_summary = (
    f"""
Baseline MAE: {baseline_mae:.6f} kWh
Baseline RMSE: {baseline_rmse:.6f} kWh
Baseline R2: {baseline_r2:.6f}
MAE improvement over baseline: {mae_improvement:.2f}%
"""
    if not np.isnan(baseline_mae)
    else "Baseline comparison file unavailable."
)

report = f"""
============================================================
WATTMinds
PREMIUM MODEL EVALUATION REPORT
============================================================

PROJECT
AI-Powered Energy Optimization and Intelligent Decision Support

EVALUATION SETUP
------------------------------------------------------------
Model: Saved Random Forest Pipeline
Test samples: {len(actual)}
Input features: {X_test.shape[1]}
Test period: {test_timestamps.min()} to {test_timestamps.max()}

PERFORMANCE METRICS
------------------------------------------------------------
MAE: {mae:.6f} kWh
RMSE: {rmse:.6f} kWh
R2 Score: {r2:.6f}
WAPE: {wape:.3f}%

MEAN CONSUMPTION
------------------------------------------------------------
Mean actual consumption: {mean_actual:.6f} kWh
Mean predicted consumption: {mean_prediction:.6f} kWh
Mean residual: {mean_error:.6f} kWh

BASELINE COMPARISON
------------------------------------------------------------
{baseline_summary}

HOURLY PERFORMANCE
------------------------------------------------------------
Lowest MAE hour: {int(best_hour['Hour_of_Day']):02d}:00
Lowest hourly MAE: {best_hour['MAE_kWh']:.6f} kWh

Highest MAE hour: {int(worst_hour['Hour_of_Day']):02d}:00
Highest hourly MAE: {worst_hour['MAE_kWh']:.6f} kWh

FEATURE IMPORTANCE
------------------------------------------------------------
{feature_summary}

INTERPRETATION
------------------------------------------------------------
MAE measures the average absolute prediction error.
RMSE penalizes larger errors more heavily.
R2 measures the model's performance relative to predicting
the mean target value on this test set.

Positive residual: actual consumption exceeded prediction.
Negative residual: prediction exceeded actual consumption.

Feature importance describes the Random Forest's reliance on
input features. It does not prove causal relationships.

LIMITATIONS
------------------------------------------------------------
Evaluation uses the existing chronological test set.
Results apply to this dataset and test period.
Further validation is needed before production deployment.
The model was not retrained during this evaluation.

============================================================
END OF REPORT
============================================================
"""

REPORT_FILE.write_text(report, encoding="utf-8")


# ============================================================
# 16. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("WATTMinds | EVALUATION RESULTS")
print("=" * 60)

print(f"MAE:  {mae:.6f} kWh")
print(f"RMSE: {rmse:.6f} kWh")
print(f"R2:   {r2:.6f}")
print(f"WAPE: {wape:.3f}%")

if not np.isnan(baseline_mae):
    print(f"Baseline MAE: {baseline_mae:.6f} kWh")
    print(f"MAE improvement: {mae_improvement:.2f}%")

print(
    f"Lowest-error hour: "
    f"{int(best_hour['Hour_of_Day']):02d}:00"
)

print(
    f"Highest-error hour: "
    f"{int(worst_hour['Hour_of_Day']):02d}:00"
)

print("\nSaved evaluation files:")

for file_path in [
    PREDICTIONS_FILE,
    METRICS_FILE,
    HOURLY_METRICS_FILE,
    REPORT_FILE,
    *PLOT_FILES.values()
]:
    if file_path.exists():
        print(file_path)

if feature_importance is not None:
    print(OUTPUT_DIR / "feature_importance.csv")

print("\nMODEL EVALUATION COMPLETED SUCCESSFULLY!")
