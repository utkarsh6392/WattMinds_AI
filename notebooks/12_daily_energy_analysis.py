
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Load hourly dataset
file_path = "data/hourly_energy_data.csv"
df = pd.read_csv(file_path)

# Step 2: Convert Hour column to datetime
df["Hour"] = pd.to_datetime(df["Hour"])

# Step 3: Create daily energy dataset
df["Date"] = df["Hour"].dt.date

daily_energy = df.groupby("Date").agg(
    Available_Hours=("Hour", "count"),
    Daily_Energy_kWh=("Energy_kWh", "sum"),
    Average_Hourly_Energy_kWh=("Energy_kWh", "mean")
).reset_index()

# Step 4: Display basic information
print("Total Daily Records:", len(daily_energy))

print("\nFirst 5 Days:")
print(daily_energy.head())

# Step 5: Analyse August 2008
daily_energy["Date"] = pd.to_datetime(daily_energy["Date"])

august_data = daily_energy[
    (daily_energy["Date"] >= "2008-08-01") &
    (daily_energy["Date"] < "2008-09-01")
]

print("\nAugust 2008 Daily Consumption:")
print(august_data.to_string(index=False))

print("\nLowest Consumption Days:")
print(
    august_data.nsmallest(10, "Daily_Energy_kWh").to_string(index=False)
)

print("\nHighest Consumption Days:")
print(
    august_data.nlargest(10, "Daily_Energy_kWh").to_string(index=False)
)

# Step 6: Plot daily consumption for August 2008
plt.figure(figsize=(14, 5))

plt.plot(
    august_data["Date"],
    august_data["Daily_Energy_kWh"],
    marker="o"
)

plt.title("Daily Electricity Consumption - August 2008")
plt.xlabel("Date")
plt.ylabel("Recorded Energy Consumption (kWh)")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()

# Step 7: Save daily dataset
output_path = "data/daily_energy_data.csv"
daily_energy.to_csv(output_path, index=False)

print("\nDaily dataset saved to:", output_path)
