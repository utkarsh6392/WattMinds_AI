
import pandas as pd
import matplotlib.pyplot as plt

file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Hour"] = pd.to_datetime(df["Hour"])

# Average energy consumption for each hour of the day
hourly_pattern = df.groupby("Hour_of_Day")["Energy_kWh"].mean()

print("Average Energy Consumption by Hour:")
print(hourly_pattern.round(3))

print("\nLowest consumption hour:")
print(hourly_pattern.idxmin(), "hour")

print("\nHighest consumption hour:")
print(hourly_pattern.idxmax(), "hour")

# Plot the daily consumption pattern
plt.figure(figsize=(12, 5))

plt.plot(
    hourly_pattern.index,
    hourly_pattern.values,
    marker="o"
)

plt.title("Average Hourly Electricity Consumption")
plt.xlabel("Hour of Day (0-23)")
plt.ylabel("Average Energy Consumption (kWh)")
plt.xticks(range(24))
plt.grid(True)
plt.tight_layout()

plt.savefig("outputs/hourly_consumption_pattern.png", dpi=150)
plt.show()
