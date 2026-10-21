
import pandas as pd
import matplotlib.pyplot as plt

file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Hour"] = pd.to_datetime(df["Hour"])

# Calculate average consumption for each month
df["Year_Month"] = df["Hour"].dt.to_period("M").astype(str)

monthly_avg = df.groupby("Year_Month")["Energy_kWh"].mean()

print("Average Energy Consumption by Month:")
print(monthly_avg.round(3))

print("\nHighest average consumption month:")
print(monthly_avg.idxmax(), ":", round(monthly_avg.max(), 3), "kWh")

print("\nLowest average consumption month:")
print(monthly_avg.idxmin(), ":", round(monthly_avg.min(), 3), "kWh")

# Plot monthly average consumption
plt.figure(figsize=(14, 5))

plt.plot(
    monthly_avg.index,
    monthly_avg.values,
    marker="o"
)

plt.title("Monthly Average Electricity Consumption")
plt.xlabel("Year-Month")
plt.ylabel("Average Energy Consumption (kWh)")
plt.xticks(rotation=60)
plt.grid(True)
plt.tight_layout()

plt.savefig("outputs/monthly_energy_analysis.png", dpi=150)
plt.show()
