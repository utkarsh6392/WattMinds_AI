from csv_processor import process_energy_csv
from energy_predictor import predict_next_hour
from energy_recommender import generate_recommendations


def predict_from_csv(file, tariff=8.0):
    """
    Process an energy CSV, predict next-hour consumption,
    and generate energy-saving recommendations.
    """

    df, features = process_energy_csv(file)

    feature_values = features.iloc[0].to_dict()
    prediction = predict_next_hour(feature_values)

    latest_hour = df["Hour"].iloc[-1]
    forecast_hour = latest_hour + __import__("pandas").Timedelta(hours=1)

    # Use the latest 24 readings from the continuous segment.
    historical_energy = df["Energy_kWh"].tail(24).tolist()

    recommendations = generate_recommendations(
        predicted_energy=prediction,
        historical_energy=historical_energy,
        tariff=tariff,
    )

    return {
        "latest_reading": latest_hour.strftime("%Y-%m-%d %H:%M"),
        "forecast_hour": forecast_hour.strftime("%Y-%m-%d %H:%M"),
        "predicted_energy_kwh": prediction,
        "recommendations": recommendations,
    }
