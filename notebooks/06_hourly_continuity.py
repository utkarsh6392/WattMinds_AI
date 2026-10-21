
import pandas as pd

file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Hour"] = pd.to_datetime(df["Hour"])
df = df.sort_values("Hour").reset_index(drop=True)

# Calculate difference between consecutive hours
df["Time_Gap"] = df["Hour"].diff()

# Find gaps greater than one hour
gaps = df[df["Time_Gap"] > pd.Timedelta(hours=1)]

print("Total hourly records:", len(df))

print("\nTime Gap Distribution:")
print(df["Time_Gap"].value_counts().head())

print("\nGaps greater than 1 hour:", len(gaps))

print("\nFirst 10 gaps:")
print(gaps[["Hour", "Time_Gap"]].head(10))

print("\nLargest gaps:")
print(
    gaps[["Hour", "Time_Gap"]]
    .sort_values("Time_Gap", ascending=False)
    .head(10)
)
