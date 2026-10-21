
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Load hourly dataset
df = pd.read_csv("data/hourly_energy_data.csv")

df["Hour"] = pd.to_datetime(df["Hour"])

# Step 2: Filter August 2008
start_date = "2008-08-01"
end_date = "2008-09-01"

august = df[
    (df["Hour"] >= start_date) &
    (df["Hour"] < end_date)
].copy()

# Step 3: Inspect hourly readings
columns = [
    "Hour",
    "Energy_kWh",
    "Global_active_power",
    "Sub_metering_1_kWh",
    "Sub_metering_2_kWh",
    "Sub_metering_3_kWh"
]

print("Total August hourly records:", len(august))

print("\nFirst 15 hourly readings:")
print(august[columns].head(15).to_string(index=False))

print("\nHourly readings on 31 August:")
print(
    august[
        august["Hour"].dt.date == pd.Timestamp("2008-08-31").date()
    ][columns].to_string(index=False)
)

# Step 4: Daily average hourly energy
august["Date"] = august["Hour"].dt.date

daily_average = august.groupby("Date")["Energy_kWh"].mean()

print("\nDaily Average Hourly Energy:")
print(daily_average.round(3).to_string())

# Step 5: Plot hourly energy for August
plt.figure(figsize=(14, 5))

plt.plot(
    august["Hour"],
    august["Energy_kWh"],
    linewidth=1
)

plt.title("Hourly Energy Consumption - August 2008")
plt.xlabel("Date and Time")
plt.ylabel("Energy Consumption (kWh)")
plt.grid(True)
plt.tight_layout()
plt.show()

# Step 6: Display summary statistics
print("\nAugust Hourly Energy Summary:")
print(august["Energy_kWh"].describe().round(3))

# Step 7: Save investigation data
august[columns].to_csv(
    "outputs/august_2008_hourly_investigation.csv",
    index=False
)

print("\nInvestigation data saved successfully.")
