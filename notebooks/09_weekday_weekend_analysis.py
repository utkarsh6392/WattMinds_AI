
import pandas as pd
import matplotlib.pyplot as plt

file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Hour"] = pd.to_datetime(df["Hour"])

# Day_of_Week: Monday = 0, Sunday = 6
df["Day_Type"] = df["Day_of_Week"].apply(
    lambda day: "Weekend" if day >= 5 else "Weekday"
)

# Compare average hourly energy consumption
comparison = df.groupby("Day_Type")["Energy_kWh"].agg(
    ["mean", "median", "count"]
)

print("Weekday vs Weekend Consumption:")
print(comparison.round(3))

# Average consumption for each day of the week
daily_pattern = df.groupby("Day_of_Week")["Energy_kWh"].mean()

day_names = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

daily_pattern.index = [
    day_names[day] for day in daily_pattern.index
]

print("\nAverage Consumption by Day:")
print(daily_pattern.round(3))

# Plot weekday vs weekend
plt.figure(figsize=(7, 5))

comparison["mean"].plot(
    kind="bar",
    rot=0
)

plt.title("Average Energy Consumption: Weekday vs Weekend")
plt.xlabel("Day Type")
plt.ylabel("Average Energy Consumption (kWh)")
plt.tight_layout()

plt.savefig("outputs/weekday_weekend_comparison.png", dpi=150)
plt.show()

# Plot individual days
plt.figure(figsize=(10, 5))

daily_pattern.plot(
    kind="bar",
    rot=30
)

plt.title("Average Energy Consumption by Day of Week")
plt.xlabel("Day")
plt.ylabel("Average Energy Consumption (kWh)")
plt.tight_layout()

plt.savefig("outputs/daily_consumption_pattern.png", dpi=150)
plt.show()
