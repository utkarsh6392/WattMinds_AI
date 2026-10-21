
import pandas as pd

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


def process_energy_csv(file):
    """
    Validate hourly energy data and generate
    features for next-hour energy prediction.
    """

    df = pd.read_csv(file)

    required_columns = ["Hour", "Energy_kWh"]
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {missing_columns}"
        )

    df = df[["Hour", "Energy_kWh"]].copy()

    df["Hour"] = pd.to_datetime(df["Hour"], errors="coerce")
    df["Energy_kWh"] = pd.to_numeric(
        df["Energy_kWh"], errors="coerce"
    )

    df = df.dropna(subset=["Hour", "Energy_kWh"])
    df = df.sort_values("Hour").reset_index(drop=True)

    if df.empty:
        raise ValueError("CSV contains no valid energy readings.")

    if (df["Energy_kWh"] < 0).any():
        raise ValueError("Energy_kWh cannot contain negative values.")

    if df["Hour"].duplicated().any():
        raise ValueError("Duplicate timestamps found in the CSV.")

    # Identify gaps between consecutive hourly readings.
    time_diff = df["Hour"].diff()
    segment_id = (~time_diff.eq(pd.Timedelta(hours=1))).cumsum()

    # Keep only the latest continuous segment.
    df["Segment_ID"] = segment_id
    latest_segment_id = df["Segment_ID"].iloc[-1]

    df = df[df["Segment_ID"] == latest_segment_id].copy()
    df = df.drop(columns=["Segment_ID"]).reset_index(drop=True)

    if len(df) < 25:
        raise ValueError(
            "The latest continuous segment contains fewer than "
            "25 hourly readings. Upload more continuous hourly data."
        )

    # Time-based features.
    df["Hour_of_Day"] = df["Hour"].dt.hour
    df["Day_of_Week"] = df["Hour"].dt.dayofweek
    df["Day_of_Month"] = df["Hour"].dt.day
    df["Month"] = df["Hour"].dt.month
    df["Is_Weekend"] = (df["Day_of_Week"] >= 5).astype(int)

    # Historical energy features.
    df["Lag_1h"] = df["Energy_kWh"].shift(1)
    df["Lag_2h"] = df["Energy_kWh"].shift(2)
    df["Lag_24h"] = df["Energy_kWh"].shift(24)

    df["Rolling_Mean_3h"] = (
        df["Energy_kWh"].shift(1).rolling(3).mean()
    )

    df["Rolling_Mean_24h"] = (
        df["Energy_kWh"].shift(1).rolling(24).mean()
    )

    latest_features = df.iloc[-1][FEATURES]

    if latest_features.isna().any():
        raise ValueError("Could not generate all required model features.")

    return df, latest_features.to_frame().T
