
import pandas as pd

file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

df["Hour"] = pd.to_datetime(df["Hour"])
df = df.sort_values("Hour")

# Generate every hourly timestamp in the dataset's date range
all_hours = pd.date_range(
    start=df["Hour"].min(),
    end=df["Hour"].max(),
    freq="h"
)

# Find timestamps that are not present in the dataset
existing_hours = pd.DatetimeIndex(df["Hour"])

missing_hours = all_hours.difference(existing_hours)

print("Expected hourly timestamps:", len(all_hours))
print("Existing hourly records:", len(existing_hours))
print("Missing hourly timestamps:", len(missing_hours))

print("\nFirst 30 missing timestamps:")
print(missing_hours[:30])

print("\nMissing hours around the largest gap:")

largest_gap_index = df["Hour"].diff().idxmax()
gap_end = df.loc[largest_gap_index, "Hour"]
gap_start = df.loc[largest_gap_index - 1, "Hour"]

print("Gap starts after:", gap_start)
print("Next available reading:", gap_end)

print("\nMissing timestamps in this gap:")
print(
    missing_hours[
        (missing_hours > gap_start) &
        (missing_hours < gap_end)
    ]
)
