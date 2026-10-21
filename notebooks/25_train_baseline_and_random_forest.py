
import pandas as pd
import numpy as np
import json

from pathlib import Path
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import joblib


# Step 1: Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

X_TRAIN_FILE = DATA_DIR / "X_train.csv"
X_TEST_FILE = DATA_DIR / "X_test.csv"
Y_TRAIN_FILE = DATA_DIR / "y_train.csv"
Y_TEST_FILE = DATA_DIR / "y_test.csv"

MODEL_FILE = MODEL_DIR / "random_forest_model.joblib"
METRICS_FILE = OUTPUT_DIR / "model_comparison.csv"
REPORT_FILE = OUTPUT_DIR / "model_training_report.txt"


# Step 2: Check input files
required_files = [
    X_TRAIN_FILE,
    X_TEST_FILE,
    Y_TRAIN_FILE,
    Y_TEST_FILE
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(f"Required file not found: {file}")


# Step 3: Load training and testing data
X_train = pd.read_csv(X_TRAIN_FILE)
X_test = pd.read_csv(X_TEST_FILE)

y_train = pd.read_csv(Y_TRAIN_FILE).squeeze("columns")
y_test = pd.read_csv(Y_TEST_FILE).squeeze("columns")

print("========== DATA LOADING ==========")
print("X_train shape:", X_train.shape)
print("X_test shape:", X_test.shape)
print("y_train shape:", y_train.shape)
print("y_test shape:", y_test.shape)


# Step 4: Validate the data
if X_train.columns.tolist() != X_test.columns.tolist():
    raise ValueError("Training and testing feature columns do not match.")

if len(X_train) != len(y_train):
    raise ValueError("Training feature and target counts do not match.")

if len(X_test) != len(y_test):
    raise ValueError("Testing feature and target counts do not match.")

if len(X_train) == 0 or len(X_test) == 0:
    raise ValueError("Training or testing dataset is empty.")

if not np.isfinite(X_train.to_numpy(dtype=float)).all():
    raise ValueError("X_train contains missing or infinite values.")

if not np.isfinite(X_test.to_numpy(dtype=float)).all():
    raise ValueError("X_test contains missing or infinite values.")

if not np.isfinite(y_train.to_numpy(dtype=float)).all():
    raise ValueError("y_train contains missing or infinite values.")

if not np.isfinite(y_test.to_numpy(dtype=float)).all():
    raise ValueError("y_test contains missing or infinite values.")


# Step 5: Define evaluation function
def evaluate_model(model_name, model, X_test, y_test):
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    return {
        "Model": model_name,
        "MAE_kWh": mae,
        "RMSE_kWh": rmse,
        "R2_Score": r2
    }


# Step 6: Train baseline model
# Predicts the average energy consumption from training data.
print("\n========== BASELINE MODEL ==========")

baseline_model = DummyRegressor(strategy="mean")
baseline_model.fit(X_train, y_train)

baseline_results = evaluate_model(
    "DummyRegressor",
    baseline_model,
    X_test,
    y_test
)

print("Baseline model trained successfully.")


# Step 7: Train Random Forest model
print("\n========== RANDOM FOREST MODEL ==========")

random_forest_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),
    (
        "model",
        RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
    )
])

random_forest_model.fit(X_train, y_train)

random_forest_results = evaluate_model(
    "RandomForestRegressor",
    random_forest_model,
    X_test,
    y_test
)

print("Random Forest model trained successfully.")


# Step 8: Compare models
results = pd.DataFrame([
    baseline_results,
    random_forest_results
])

print("\n========== MODEL COMPARISON ==========")
print(results.to_string(index=False))


# Step 9: Save comparison metrics
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results.to_csv(METRICS_FILE, index=False)

# Step 10: Save trained Random Forest model
joblib.dump(random_forest_model, MODEL_FILE)


# Step 11: Save training report
best_model_row = results.loc[results["MAE_kWh"].idxmin()]

report = f"""
WATTMinds - MODEL TRAINING REPORT

Task:
Predict next-hour electricity consumption.

Target:
Target_Next_Hour_kWh

Training rows:
{len(X_train)}

Testing rows:
{len(X_test)}

Input features:
{X_train.columns.tolist()}

Model 1:
DummyRegressor(strategy='mean')

Model 2:
RandomForestRegressor(
    n_estimators=150,
    max_depth=15,
    min_samples_leaf=2,
    random_state=42
)

Evaluation metrics:
MAE  = Mean Absolute Error, measured in kWh
RMSE = Root Mean Squared Error, measured in kWh
R2   = R-squared score

Model comparison:
{results.to_string(index=False)}

Lowest test MAE:
{best_model_row['Model']}

Lowest MAE value:
{best_model_row['MAE_kWh']:.6f} kWh

Note:
The model with the lowest MAE has the lowest average absolute
prediction error on this test set. Further validation is needed
before selecting a final production model.
"""

REPORT_FILE.write_text(report, encoding="utf-8")


# Step 12: Display saved files
print("\n========== SAVED FILES ==========")
print("Model:", MODEL_FILE)
print("Metrics:", METRICS_FILE)
print("Report:", REPORT_FILE)

print("\nMODEL TRAINING COMPLETED SUCCESSFULLY!")
