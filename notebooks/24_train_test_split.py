
import pandas as pd
from pathlib import Path

# Step 1: Define project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "ml_ready_dataset.csv"

X_TRAIN_FILE = PROJECT_ROOT / "data" / "X_train.csv"
X_TEST_FILE = PROJECT_ROOT / "data" / "X_test.csv"

Y_TRAIN_FILE = PROJECT_ROOT / "data" / "y_train.csv"
Y_TEST_FILE = PROJECT_ROOT / "data" / "y_test.csv"

REPORT_FILE = PROJECT_ROOT / "outputs" / "train_test_split_report.txt"

# Step 2: Check input file
if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"ML-ready dataset not found: {INPUT_FILE}"
    )

# Step 3: Load ML-ready dataset
df = pd.read_csv(INPUT_FILE, parse_dates=["Hour"])

print("Dataset shape:", df.shape)

# Step 4: Validate dataset
target_column = "Target_Next_Hour_kWh"

if target_column not in df.columns:
    raise ValueError(f"Target column '{target_column}' not found.")

if "Hour" not in df.columns:
    raise ValueError("Hour column not found.")

if df["Hour"].duplicated().any():
    raise ValueError("Duplicate timestamps found.")

if not df["Hour"].is_monotonic_increasing:
    raise ValueError("Dataset is not in chronological order.")

if df.isna().any().any():
    raise ValueError("Missing values found in the dataset.")

# Step 5: Separate features and target
# Hour is retained separately for chronological verification,
# but it is not used as a model input feature.
feature_columns = [
    column
    for column in df.columns
    if column not in ["Hour", target_column]
]

X = df[feature_columns]
y = df[[target_column]]

timestamps = df["Hour"]

print("\nNumber of input features:", len(feature_columns))
print("Feature columns:", feature_columns)
print("Target column:", target_column)

# Step 6: Chronological 80/20 split
# No random shuffle: earlier records train the model,
# later records test its performance.
split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index].copy()
X_test = X.iloc[split_index:].copy()

y_train = y.iloc[:split_index].copy()
y_test = y.iloc[split_index:].copy()

train_timestamps = timestamps.iloc[:split_index]
test_timestamps = timestamps.iloc[split_index:]

# Step 7: Validate split
if len(X_train) == 0 or len(X_test) == 0:
    raise ValueError("Training or testing dataset is empty.")

if len(X_train) != len(y_train):
    raise ValueError("Training features and target row counts differ.")

if len(X_test) != len(y_test):
    raise ValueError("Testing features and target row counts differ.")

if train_timestamps.max() >= test_timestamps.min():
    raise ValueError("Chronological split validation failed.")

# Step 8: Save the four datasets
X_TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

X_train.to_csv(X_TRAIN_FILE, index=False)
X_test.to_csv(X_TEST_FILE, index=False)

y_train.to_csv(Y_TRAIN_FILE, index=False)
y_test.to_csv(Y_TEST_FILE, index=False)

# Step 9: Save split report
report = f"""
WATTMinds - TRAIN TEST SPLIT REPORT

Input dataset:
{INPUT_FILE.name}

Split method:
Chronological split (no random shuffle)

Training percentage:
80%

Testing percentage:
20%

Total rows:
{len(df)}

Training rows:
{len(X_train)}

Testing rows:
{len(X_test)}

Number of features:
{len(feature_columns)}

Feature columns:
{feature_columns}

Target column:
{target_column}

Training period:
{train_timestamps.min()} to {train_timestamps.max()}

Testing period:
{test_timestamps.min()} to {test_timestamps.max()}

Missing values in X_train:
{int(X_train.isna().sum().sum())}

Missing values in X_test:
{int(X_test.isna().sum().sum())}

Missing values in y_train:
{int(y_train.isna().sum().sum())}

Missing values in y_test:
{int(y_test.isna().sum().sum())}

Model training:
Not performed in this step.
"""

REPORT_FILE.write_text(report, encoding="utf-8")

# Step 10: Display results
print("\n========== TRAIN TEST SPLIT ==========")

print("\nX_train shape:", X_train.shape)
print("X_test shape:", X_test.shape)

print("y_train shape:", y_train.shape)
print("y_test shape:", y_test.shape)

print("\nTraining period:")
print(train_timestamps.min(), "to", train_timestamps.max())

print("\nTesting period:")
print(test_timestamps.min(), "to", test_timestamps.max())

print("\nSaved files:")
print(X_TRAIN_FILE)
print(X_TEST_FILE)
print(Y_TRAIN_FILE)
print(Y_TEST_FILE)
print(REPORT_FILE)

print("\nTRAIN TEST SPLIT COMPLETED SUCCESSFULLY!")
