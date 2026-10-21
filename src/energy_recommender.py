
def generate_recommendations(predicted_energy, historical_energy, tariff=8.0):
    """
    Generate basic energy-saving recommendations
    using predicted and recent historical consumption.
    """

    if not historical_energy:
        raise ValueError("Historical energy readings are required.")

    average_energy = sum(historical_energy) / len(historical_energy)

    estimated_cost = predicted_energy * tariff

    if average_energy <= 0:
        level = "Insufficient baseline"
        recommendation = (
            "Historical average is zero or below. "
            "Collect more reliable readings before comparing usage."
        )

    elif predicted_energy >= average_energy * 1.50:
        level = "Unusually high"
        recommendation = (
            "Predicted usage is substantially above the recent average. "
            "Review expected appliance usage and avoid unnecessary loads."
        )

    elif predicted_energy >= average_energy * 1.25:
        level = "High"
        recommendation = (
            "Predicted usage is above the recent average. "
            "Consider shifting flexible electricity use where practical."
        )

    elif predicted_energy <= average_energy * 0.75:
        level = "Low"
        recommendation = (
            "Predicted usage is below the recent average. "
            "Continue monitoring to confirm this pattern."
        )

    else:
        level = "Normal"
        recommendation = (
            "Predicted usage is near the recent average. "
            "Continue following energy-efficient habits."
        )

    savings_scenarios = []

    for reduction_percent in [5, 10, 15]:
        energy_saved = predicted_energy * reduction_percent / 100

        savings_scenarios.append({
            "reduction_percent": reduction_percent,
            "estimated_energy_saved_kwh": round(energy_saved, 4),
            "estimated_cost_saved": round(energy_saved * tariff, 2),
        })

    return {
        "consumption_level": level,
        "predicted_energy_kwh": round(predicted_energy, 4),
        "estimated_cost_rs": round(estimated_cost, 2),
        "historical_average_kwh": round(average_energy, 4),
        "recommendation": recommendation,
        "savings_scenarios": savings_scenarios,
        "tariff_rs_per_kwh": tariff,
    }
