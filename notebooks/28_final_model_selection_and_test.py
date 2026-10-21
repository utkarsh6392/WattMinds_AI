
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------------------
# STEP 1: PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

X_TRAIN_PATH = DATA_DIR / "X_train.csv"
Y_TRAIN_PATH = DATA_DIR / "y_train.csv"
X_TEST_PATH = DATA_DIR / "X_test.csv"
Y_TEST_PATH = DATA_DIR / "y_test.csv"

RF_MODEL_PATH = MODEL_DIR / "random_forest_model.joblib"
ML_DATA_PATH = DATA_DIR / "ml_ready_dataset.csv"


# --------------------------------------------------
# STEP 2: LOAD DATA
# --------------------------------------------------

print("\n" + "=" * 65)
print("WATTMinds - FINAL MODEL SELECTION AND TEST")
print("=" * 65)

X_train = pd.read_csv(X_TRAIN_PATH)
y_train = pd.read_csv(Y_TRAIN_PATH).squeeze("columns")

X_test = pd.read_csv(X_TEST_PATH)
y_test = pd.read_csv(Y_TEST_PATH).squeeze("columns")

print("\nTraining features:", X_train.shape)
print("Testing features:", X_test.shape)

if list(X_train.columns) != list(X_test.columns):
    raise ValueError("Training and test feature columns do not match.")

if len(X_test) != len(y_test):
    raise ValueError("X_test and y_test have different row counts.")


# --------------------------------------------------
# STEP 3: LOAD EXISTING RANDOM FOREST
# --------------------------------------------------

if not RF_MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Random Forest model not found: {RF_MODEL_PATH}"
    )

random_forest_model = joblib.load(RF_MODEL_PATH)


# --------------------------------------------------
# STEP 4: CREATE FINAL HIST GRADIENT BOOSTING MODEL
# --------------------------------------------------

print("\nTraining final Hist Gradient Boosting model...")

final_model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("model", HistGradientBoostingRegressor(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=20,
        l2_regularization=1.0,
        random_state=42
    ))
])

start_time = time.time()

# Retrain using all available training data.
# The final test data is not used for training.
final_model.fit(X_train, y_train)

training_seconds = time.time() - start_time

print(f"Training completed in {training_seconds:.2f} seconds.")


# --------------------------------------------------
# STEP 5: PREDICT ON THE UNTOUCHED TEST SET
# --------------------------------------------------

print("\nEvaluating both models on the final test set...")

rf_predictions = random_forest_model.predict(X_test)
hgb_predictions = final_model.predict(X_test)


# --------------------------------------------------
# STEP 6: CALCULATE METRICS
# --------------------------------------------------

def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    r2 = r2_score(actual, predicted)

    actual_sum = np.abs(np.asarray(actual)).sum()

    if actual_sum == 0:
        wape = np.nan
    else:
        wape = (
            np.abs(np.asarray(actual) - np.asarray(predicted)).sum()
            / actual_sum
        ) * 100

    return {
        "MAE_kWh": mae,
        "RMSE_kWh": rmse,
        "R2": r2,
        "WAPE_percent": wape
    }


rf_metrics = calculate_metrics(y_test, rf_predictions)
hgb_metrics = calculate_metrics(y_test, hgb_predictions)

comparison = pd.DataFrame([
    {
        "Model": "Random Forest",
        **rf_metrics
    },
    {
        "Model": "Hist Gradient Boosting",
        **hgb_metrics
    }
])

comparison_path = OUTPUT_DIR / "final_test_model_comparison.csv"
comparison.to_csv(comparison_path, index=False)


# --------------------------------------------------
# STEP 7: PRINT FINAL RESULTS
# --------------------------------------------------

print("\n" + "=" * 65)
print("FINAL TEST RESULTS")
print("=" * 65)

print(comparison.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

rf_mae = rf_metrics["MAE_kWh"]
hgb_mae = hgb_metrics["MAE_kWh"]

if rf_mae != 0:
    mae_change_percent = ((rf_mae - hgb_mae) / rf_mae) * 100
else:
    mae_change_percent = np.nan

if hgb_mae < rf_mae:
    decision = "Hist Gradient Boosting"
elif rf_mae < hgb_mae:
    decision = "Random Forest"
else:
    decision = "Both models have equal MAE"

print("\nModel with lower final test MAE:", decision)
print(f"MAE change vs Random Forest: {mae_change_percent:.2f}%")
print(f"Final model training time: {training_seconds:.2f} seconds")


# --------------------------------------------------
# STEP 8: SAVE FINAL MODEL
# --------------------------------------------------

FINAL_MODEL_PATH = MODEL_DIR / "final_energy_prediction_model.joblib"

# Save the model selected through validation.
# The test set is used only for evaluation, not selection.
joblib.dump(final_model, FINAL_MODEL_PATH)

print("\nSaved final Hist Gradient Boosting model:")
print(FINAL_MODEL_PATH)


# --------------------------------------------------
# STEP 9: SAVE TEST PREDICTIONS
# --------------------------------------------------

predictions_df = pd.DataFrame({
    "Actual_Energy_kWh": np.asarray(y_test),
    "Random_Forest_Prediction_kWh": rf_predictions,
    "Hist_Gradient_Boosting_Prediction_kWh": hgb_predictions,
    "RF_Absolute_Error_kWh": np.abs(
        np.asarray(y_test) - rf_predictions
    ),
    "HGB_Absolute_Error_kWh": np.abs(
        np.asarray(y_test) - hgb_predictions
    )
})

# Attach timestamps if the ML-ready dataset contains them.
if ML_DATA_PATH.exists():
    ml_data = pd.read_csv(ML_DATA_PATH)

    timestamp_candidates = [
        "Target_Timestamp",
        "Timestamp",
        "Datetime",
        "Hour"
    ]

    timestamp_column = next(
        (column for column in timestamp_candidates
         if column in ml_data.columns),
        None
    )

    if timestamp_column is not None and len(ml_data) >= len(X_test):
        test_timestamps = ml_data[timestamp_column].iloc[-len(X_test):]
        predictions_df.insert(
            0,
            timestamp_column,
            test_timestamps.reset_index(drop=True)
        )
    else:
        predictions_df.insert(
            0,
            "Test_Row",
            np.arange(1, len(predictions_df) + 1)
        )
else:
    predictions_df.insert(
        0,
        "Test_Row",
        np.arange(1, len(predictions_df) + 1)
    )

predictions_path = OUTPUT_DIR / "final_test_predictions.csv"
predictions_df.to_csv(predictions_path, index=False)


# --------------------------------------------------
# STEP 10: SAVE FINAL REPORT
# --------------------------------------------------

report_path = OUTPUT_DIR / "final_model_evaluation_report.txt"

with open(report_path, "w", encoding="utf-8") as file:
    file.write("WATTMinds - FINAL MODEL EVALUATION REPORT\n")
    file.write("=" * 65 + "\n\n")

    file.write(f"Training rows: {len(X_train)}\n")
    file.write(f"Final test rows: {len(X_test)}\n")
    file.write(f"Training time: {training_seconds:.2f} seconds\n\n")

    file.write("Final test comparison:\n")
    file.write(comparison.to_string(index=False))
    file.write("\n\n")

    file.write(f"Model with lower final test MAE: {decision}\n")
    file.write(f"MAE change vs Random Forest: {mae_change_percent:.2f}%\n\n")

    file.write(
        "Important: Hist Gradient Boosting was selected based on "
        "chronological validation MAE. The final test set was not "
        "used for model training or model selection.\n"
    )

print("\nSaved comparison:", comparison_path)
print("Saved predictions:", predictions_path)
print("Saved report:", report_path)


# --------------------------------------------------
# STEP 11: CREATE ACTUAL VS PREDICTED GRAPH
# --------------------------------------------------

plt.figure(figsize=(12, 6))

sample_size = min(300, len(y_test))

plt.plot(
    np.asarray(y_test)[:sample_size],
    label="Actual Energy",
    linewidth=2
)

plt.plot(
    hgb_predictions[:sample_size],
    label="Hist Gradient Boosting",
    linewidth=1.5
)

plt.title("Actual vs Predicted Energy - Final Test Sample")
plt.xlabel("Test Sample")
plt.ylabel("Energy (kWh)")
plt.legend()
plt.tight_layout()

graph_path = OUTPUT_DIR / "final_actual_vs_predicted.png"
plt.savefig(graph_path, dpi=300)
plt.close()

print("Saved graph:", graph_path)

print("\nFinal evaluation completed successfully.")
