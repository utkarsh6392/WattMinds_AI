
import pandas as pd

file_path = "data/household_power_consumption_cleaned.csv"

df = pd.read_csv(file_path)

# Convert Datetime column
df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")

# Sort readings by time
df = df.sort_values("Datetime").reset_index(drop=True)

# Calculate time difference between consecutive readings
df["Time_Difference"] = df["Datetime"].diff()

print("First 10 time differences:")
print(df[["Datetime", "Time_Difference"]].head(10))

# Count gaps greater than one minute
gaps = df[df["Time_Difference"] > pd.Timedelta(minutes=1)]

print("\nTotal gaps greater than 1 minute:", len(gaps))

# Show first 20 gaps
print("\nFirst 20 gaps:")
print(gaps[["Datetime", "Time_Difference"]].head(20))

# Show the largest gaps
print("\n10 Largest time gaps:")
print(
    gaps[["Datetime", "Time_Difference"]]
    .sort_values("Time_Difference", ascending=False)
    .head(10)
)
