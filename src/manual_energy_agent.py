
import pandas as pd


def run_energy_agent(appliances, tariff, target_savings=500.0):
    df = appliances.copy()

    required = [
        "Appliance",
        "Rated Power (W)",
        "Hours/Day",
        "Quantity",
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    for column in ["Rated Power (W)", "Hours/Day", "Quantity"]:
        df[column] = pd.to_numeric(df[column], errors="raise")

    if df.empty:
        raise ValueError("Add at least one appliance.")

    if (df["Rated Power (W)"] < 0).any():
        raise ValueError("Power cannot be negative.")

    if not df["Hours/Day"].between(0, 24).all():
        raise ValueError("Usage hours must be between 0 and 24.")

    if not df["Quantity"].between(1, 100).all():
        raise ValueError("Quantity must be between 1 and 100.")

    if tariff < 0 or target_savings < 0:
        raise ValueError("Tariff and savings target cannot be negative.")

    df["Daily Energy (kWh)"] = (
        df["Rated Power (W)"]
        * df["Hours/Day"]
        * df["Quantity"]
        / 1000
    )

    df["Monthly Energy (kWh)"] = (
        df["Daily Energy (kWh)"] * 30
    )

    df["Monthly Cost (₹)"] = (
        df["Monthly Energy (kWh)"] * tariff
    )

    total_daily = float(df["Daily Energy (kWh)"].sum())
    total_monthly = float(df["Monthly Energy (kWh)"].sum())
    total_cost = float(df["Monthly Cost (₹)"].sum())

    if total_monthly > 0:
        df["Energy Share (%)"] = (
            df["Monthly Energy (kWh)"] / total_monthly * 100
        )
    else:
        df["Energy Share (%)"] = 0.0

    ranked = df.sort_values(
        "Monthly Energy (kWh)", ascending=False
    )

    recommendations = []

    for _, row in ranked.iterrows():
        watts = float(row["Rated Power (W)"])
        hours = float(row["Hours/Day"])
        quantity = int(row["Quantity"])

        share = float(row["Energy Share (%)"])
        priority = (
            "High" if share >= 30
            else "Medium" if share >= 10
            else "Low"
        )

        reduction_hours = min(hours * 0.20, 2.0)
        saved_energy = (
            watts * reduction_hours * quantity * 30 / 1000
        )
        saved_cost = saved_energy * tariff

        recommendations.append({
            "Appliance": str(row["Appliance"]),
            "Priority": priority,
            "Monthly Energy (kWh)": round(
                float(row["Monthly Energy (kWh)"]), 2
            ),
            "Monthly Cost (₹)": round(
                float(row["Monthly Cost (₹)"]), 2
            ),
            "Energy Share (%)": round(share, 1),
            "Suggested Hours Reduction/Day": round(
                reduction_hours, 2
            ),
            "Potential Monthly Savings (₹)": round(
                saved_cost, 2
            ),
            "Recommended Action": (
                f"Consider reducing usage by {reduction_hours:.1f} "
                "hour(s) per day if practical and safe."
                if reduction_hours > 0
                else "No usage reduction scenario available."
            ),
        })

    recommendations.sort(
        key=lambda item: item["Potential Monthly Savings (₹)"],
        reverse=True,
    )

    action_plan = []
    projected_savings = 0.0

    for item in recommendations:
        saving = item["Potential Monthly Savings (₹)"]

        if saving <= 0 or projected_savings >= target_savings:
            continue

        action_plan.append({
            "Appliance": item["Appliance"],
            "Action": item["Recommended Action"],
            "Potential Monthly Savings (₹)": saving,
        })

        projected_savings += saving

    if total_monthly > 0:
        top = ranked.iloc[0]
        top_name = str(top["Appliance"])
        summary = (
            f"{top_name} is the highest energy-consuming appliance "
            f"among your entries, using an estimated "
            f"{top['Monthly Energy (kWh)']:.2f} kWh/month "
            f"({top['Energy Share (%)']:.1f}% of entered usage)."
        )
    else:
        top_name = None
        summary = (
            "No energy consumption was calculated. "
            "Enter positive power ratings and usage hours."
        )

    return {
        "summary": summary,
        "top_appliance": top_name,
        "total_daily_energy_kwh": round(total_daily, 2),
        "total_monthly_energy_kwh": round(total_monthly, 2),
        "total_monthly_cost": round(total_cost, 2),
        "target_savings": round(float(target_savings), 2),
        "projected_savings": round(projected_savings, 2),
        "target_achieved": projected_savings >= target_savings,
        "analysis": df.round(2),
        "recommendations": recommendations,
        "action_plan": action_plan,
    }
