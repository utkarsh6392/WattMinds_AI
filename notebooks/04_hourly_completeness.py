
import pandas as pd

file_path = "data/household_power_consumption_cleaned.csv"

df = pd.read_csv(file_path)

df["Datetime"] = pd.to_datetime(
    df["Datetime"],
    errors="coerce"
)

df = df.dropna(subset=["Datetime"])
df = df.sort_values("Datetime")

# Create an hourly group for each reading
df["Hour"] = df["Datetime"].dt.floor("h")

# Count recorded minute-level readings in each hour
hourly_counts = df.groupby("Hour").size()

print("Total hourly groups:", len(hourly_counts))

print("\nReadings per hour distribution:")
print(hourly_counts.value_counts().sort_index())

# A complete hour should have 60 readings
complete_hours = (hourly_counts == 60).sum()
partial_hours = (hourly_counts < 60).sum()

print("\nComplete hours:", complete_hours)
print("Partial hours:", partial_hours)

print("\nFirst 10 partial hours:")
print(hourly_counts[hourly_counts < 60].head(10))
