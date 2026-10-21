
import pandas as pd
import matplotlib.pyplot as plt

# Load hourly dataset
df = pd.read_csv("data/hourly_energy_data.csv")

# Convert Hour column into datetime
df["Hour"] = pd.to_datetime(df["Hour"])

# Select July, August and September 2008
start_date = "2008-07-01"
end_date = "2008-10-01"

comparison = df[
    (df["Hour"] >= start_date) &
    (df["Hour"] < end_date)
].copy()

# Create year-month column
comparison["Year_Month"] = comparison["Hour"].dt.to_period("M").astype(str)

# Monthly statistics
monthly_stats = comparison.groupby("Year_Month").agg(
    Available_Hours=("Energy_kWh", "count"),
    Average_Energy_kWh=("Energy_kWh", "mean"),
    Median_Energy_kWh=("Energy_kWh", "median"),
    Total_Energy_kWh=("Energy_kWh", "sum"),
    Maximum_Energy_kWh=("Energy_kWh", "max")
).round(3)

print("\nMONTHLY CONSUMPTION COMPARISON")
print("=" * 75)
print(monthly_stats)

# Plot comparison
monthly_stats["Average_Energy_kWh"].plot(
    kind="bar",
    figsize=(9, 5),
    title="Average Hourly Energy: July–September 2008"
)

plt.xlabel("Month")
plt.ylabel("Average Energy (kWh)")
plt.xticks(rotation=0)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/july_august_september_comparison.png", dpi=300)
plt.show()

print("\nChart saved to outputs/july_august_september_comparison.png")
