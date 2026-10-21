
from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "final_energy_prediction_model.joblib"
)

FEATURES = [
    "Hour_of_Day",
    "Day_of_Week",
    "Day_of_Month",
    "Month",
    "Is_Weekend",
    "Lag_1h",
    "Lag_2h",
    "Lag_24h",
    "Rolling_Mean_3h",
    "Rolling_Mean_24h",
]


def predict_next_hour(feature_values):
    """
    Predict next-hour electricity consumption in kWh.

    feature_values must contain the 10 model features.
    """

    model = joblib.load(MODEL_PATH)

    # Convert input into a one-row DataFrame
    input_data = pd.DataFrame(
        [feature_values],
        columns=FEATURES
    )

    # Run prediction
    prediction = model.predict(input_data)[0]

    # Energy consumption cannot be negative
    prediction = max(0.0, float(prediction))

    return round(prediction, 4)
