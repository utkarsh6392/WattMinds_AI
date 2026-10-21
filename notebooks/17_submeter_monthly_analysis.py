
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/hourly_energy_data.csv")
df["Hour"] = pd.to_datetime(df["Hour"])
df["Year_Month"] = df["Hour"].dt.to_period("M").astype(str)

months = ["2008-07", "2008-08", "2008-09"]
data = df[df["Year_Month"].isin(months)].copy()

columns = [
    "Energy_kWh",
    "Sub_metering_1_kWh",
    "Sub_metering_2_kWh",
    "Sub_metering_3_kWh"
]

monthly_avg = data.groupby("Year_Month")[columns].mean().round(4)

print("\nMONTHLY ENERGY AND SUB-METER COMPARISON")
print("=" * 75)
print(monthly_avg)

# Plot average consumption for each category
monthly_avg.plot(
    kind="bar",
    figsize=(11, 6)
)

plt.title("Monthly Average Energy and Sub-meter Readings")
plt.xlabel("Month")
plt.ylabel("Average hourly value (kWh)")
plt.xticks(rotation=0)
plt.legend(title="Measurement")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    "outputs/monthly_submeter_comparison.png",
    dpi=300
)
plt.show()

print("\nChart saved to outputs/monthly_submeter_comparison.png")
