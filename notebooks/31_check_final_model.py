
from pathlib import Path
import joblib

# Project root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the trained model
model_path = BASE_DIR / "models" / "final_energy_prediction_model.joblib"
model = joblib.load(model_path)

print("Model loaded successfully!")
print("Model type:", type(model).__name__)

# Check expected input features
if hasattr(model, "n_features_in_"):
    print("Number of expected features:", model.n_features_in_)

if hasattr(model, "feature_names_in_"):
    print("\nExpected feature names:")
    for feature in model.feature_names_in_:
        print("-", feature)
else:
    print("\nModel does not store feature names.")
    print("We will verify the training dataset columns next.")
