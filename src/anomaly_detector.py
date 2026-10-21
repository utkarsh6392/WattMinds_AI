
import pandas as pd
import numpy as np


def detect_energy_anomalies(
    data,
    column="Energy_kWh",
    window=24,
    threshold=3.0
):
    """
    Detect unusually high or low energy consumption
    using a rolling median and Median Absolute Deviation.
    """

    if column not in data.columns:
        raise ValueError(
            f"Required column '{column}' was not found."
        )

    result = data.copy()

    result[column] = pd.to_numeric(
        result[column], errors="coerce"
    )

    result = result.dropna(subset=[column]).reset_index(drop=True)

    if result.empty:
        raise ValueError("No valid energy readings found.")

    if window < 3:
        raise ValueError("Window must be at least 3.")

    if threshold <= 0:
        raise ValueError("Threshold must be greater than 0.")

    # Use only previous readings to establish the baseline.
    previous_values = result[column].shift(1)

    rolling_median = previous_values.rolling(
        window=window,
        min_periods=window
    ).median()

    absolute_deviation = (
        previous_values - rolling_median
    ).abs()

    rolling_mad = absolute_deviation.rolling(
        window=window,
        min_periods=window
    ).median()

    # Robust estimate of variation.
    robust_std = 1.4826 * rolling_mad

    difference = result[column] - rolling_median

    result["Expected_Energy_kWh"] = rolling_median
    result["Deviation_kWh"] = difference

    result["Anomaly_Score"] = np.where(
        robust_std > 0,
        difference.abs() / robust_std,
        np.where(difference.abs() > 0, np.inf, 0.0)
    )

    result["Anomaly"] = (
        (result["Anomaly_Score"] > threshold)
        & rolling_median.notna()
    )

    result["Anomaly_Type"] = np.select(
        [
            result["Anomaly"] & (difference > 0),
            result["Anomaly"] & (difference < 0)
        ],
        [
            "Unusually High Consumption",
            "Unusually Low Consumption"
        ],
        default="Normal"
    )

    return result
