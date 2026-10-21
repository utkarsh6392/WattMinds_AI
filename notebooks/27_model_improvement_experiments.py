
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor
)
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

BASE_MODEL_PATH = MODEL_DIR / "random_forest_model.joblib"


# --------------------------------------------------
# STEP 2: LOAD TRAINING DATA
# --------------------------------------------------

print("\n" + "=" * 60)
print("WATTMinds - MODEL IMPROVEMENT EXPERIMENTS")
print("=" * 60)

X_train = pd.read_csv(X_TRAIN_PATH)
y_train = pd.read_csv(Y_TRAIN_PATH).squeeze("columns")

X_test = pd.read_csv(X_TEST_PATH)
y_test = pd.read_csv(Y_TEST_PATH).squeeze("columns")

print("\nTraining data shape:", X_train.shape)
print("Test data shape:", X_test.shape)


# --------------------------------------------------
# STEP 3: CREATE CHRONOLOGICAL VALIDATION SPLIT
# --------------------------------------------------

# Last 20% of training data will be used for validation.
# Rows are already in chronological order.

split_index = int(len(X_train) * 0.80)

X_subtrain = X_train.iloc[:split_index].copy()
y_subtrain = y_train.iloc[:split_index].copy()

X_validation = X_train.iloc[split_index:].copy()
y_validation = y_train.iloc[split_index:].copy()

print("\nSub-training rows:", len(X_subtrain))
print("Validation rows:", len(X_validation))
print("Final test rows kept untouched:", len(X_test))


# --------------------------------------------------
# STEP 4: DEFINE MODELS
# --------------------------------------------------

models = {
    "Random Forest": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ]),

    "Extra Trees": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", ExtraTreesRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ]),

    "Hist Gradient Boosting": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=20,
            l2_regularization=1.0,
            random_state=42
        ))
    ])
}


# --------------------------------------------------
# STEP 5: TRAIN AND VALIDATE MODELS
# --------------------------------------------------

results = []
trained_models = {}

for model_name, model in models.items():

    print(f"\nTraining: {model_name}")
    start_time = time.time()

    model.fit(X_subtrain, y_subtrain)

    predictions = model.predict(X_validation)

    mae = mean_absolute_error(y_validation, predictions)
    rmse = np.sqrt(mean_squared_error(y_validation, predictions))
    r2 = r2_score(y_validation, predictions)

    elapsed_time = time.time() - start_time

    results.append({
        "Model": model_name,
        "Validation_MAE_kWh": mae,
        "Validation_RMSE_kWh": rmse,
        "Validation_R2": r2,
        "Training_Time_Seconds": elapsed_time
    })

    trained_models[model_name] = model

    print(f"Validation MAE:  {mae:.6f} kWh")
    print(f"Validation RMSE: {rmse:.6f} kWh")
    print(f"Validation R2:   {r2:.6f}")
    print(f"Training time:   {elapsed_time:.2f} seconds")


# --------------------------------------------------
# STEP 6: SAVE VALIDATION COMPARISON
# --------------------------------------------------

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="Validation_MAE_kWh",
    ascending=True
).reset_index(drop=True)

results_path = OUTPUT_DIR / "model_improvement_comparison.csv"
results_df.to_csv(results_path, index=False)

print("\n" + "=" * 60)
print("VALIDATION MODEL COMPARISON")
print("=" * 60)

print(results_df.to_string(index=False))

best_model_name = results_df.iloc[0]["Model"]
best_validation_mae = results_df.iloc[0]["Validation_MAE_kWh"]

print("\nBest validation model:", best_model_name)
print(f"Best validation MAE: {best_validation_mae:.6f} kWh")


# --------------------------------------------------
# STEP 7: SAVE BEST VALIDATION MODEL
# --------------------------------------------------

best_model = trained_models[best_model_name]

best_model_path = MODEL_DIR / "best_validation_model.joblib"

joblib.dump(best_model, best_model_path)


# --------------------------------------------------
# STEP 8: SAVE EXPERIMENT REPORT
# --------------------------------------------------

report_path = OUTPUT_DIR / "model_improvement_report.txt"

with open(report_path, "w", encoding="utf-8") as file:

    file.write("WATTMinds - MODEL IMPROVEMENT EXPERIMENTS\n")
    file.write("=" * 60 + "\n\n")

    file.write("Validation strategy: Chronological split\n")
    file.write("Sub-training fraction: 80% of original training set\n")
    file.write("Validation fraction: 20% of original training set\n")
    file.write("Final test set: Not used for model selection\n\n")

    file.write("Model comparison:\n")
    file.write(results_df.to_string(index=False))
    file.write("\n\n")

    file.write(f"Best validation model: {best_model_name}\n")
    file.write(f"Best validation MAE: {best_validation_mae:.6f} kWh\n\n")

    file.write(
        "Note: The best model is selected using validation MAE. "
        "Its performance must be confirmed later on the untouched "
        "final test set before making final claims.\n"
    )

print("\nSaved comparison:", results_path)
print("Saved report:", report_path)
print("Saved best validation model:", best_model_path)

print("\nExperiment completed successfully.")

