
import pandas as pd

file_path = "data/household_power_consumption_cleaned.csv"
output_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Datetime"] = pd.to_datetime(
    df["Datetime"],
    errors="coerce"
)

df = df.dropna(subset=["Datetime"])
df = df.sort_values("Datetime")

# Create hourly groups
df["Hour"] = df["Datetime"].dt.floor("h")

# Count minute-level readings in each hour
hourly_counts = df.groupby("Hour").size()

# Keep only hours with all 60 readings
complete_hours = hourly_counts[hourly_counts == 60].index

df = df[df["Hour"].isin(complete_hours)].copy()

# Aggregate minute-level readings into hourly data
hourly_df = df.groupby("Hour").agg(
    Global_active_power=("Global_active_power", "sum"),
    Global_reactive_power=("Global_reactive_power", "mean"),
    Voltage=("Voltage", "mean"),
    Global_intensity=("Global_intensity", "mean"),
    Sub_metering_1=("Sub_metering_1", "sum"),
    Sub_metering_2=("Sub_metering_2", "sum"),
    Sub_metering_3=("Sub_metering_3", "sum")
).reset_index()

# Convert units
hourly_df["Energy_kWh"] = (
    hourly_df["Global_active_power"] / 60
)

hourly_df["Sub_metering_1_kWh"] = (
    hourly_df["Sub_metering_1"] / 1000
)

hourly_df["Sub_metering_2_kWh"] = (
    hourly_df["Sub_metering_2"] / 1000
)

hourly_df["Sub_metering_3_kWh"] = (
    hourly_df["Sub_metering_3"] / 1000
)

# Add time-based features
hourly_df["Hour_of_Day"] = hourly_df["Hour"].dt.hour
hourly_df["Day_of_Week"] = hourly_df["Hour"].dt.dayofweek
hourly_df["Month"] = hourly_df["Hour"].dt.month

# Save hourly dataset
hourly_df.to_csv(output_path, index=False)

print("Hourly dataset created successfully!")
print("Shape:", hourly_df.shape)

print("\nFirst 5 rows:")
print(hourly_df.head())

print("\nMissing values:")
print(hourly_df.isnull().sum())

print("\nSaved to:", output_path)
