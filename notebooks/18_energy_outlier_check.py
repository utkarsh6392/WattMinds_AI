
import pandas as pd

df = pd.read_csv("data/hourly_energy_data.csv")
df["Hour"] = pd.to_datetime(df["Hour"])

# Compare August with the rest of the dataset
august = df[
    (df["Hour"] >= "2008-08-01") &
    (df["Hour"] < "2008-09-01")
].copy()

other = df[
    ~(
        (df["Hour"] >= "2008-08-01") &
        (df["Hour"] < "2008-09-01")
    )
].copy()

print("\nENERGY DISTRIBUTION CHECK")
print("=" * 65)

print("\nAugust statistics:")
print(august["Energy_kWh"].describe().round(3))

print("\nRest of dataset statistics:")
print(other["Energy_kWh"].describe().round(3))

# Check August's highest readings
print("\nHighest 10 August hourly readings:")
print(
    august.nlargest(10, "Energy_kWh")[
        ["Hour", "Energy_kWh", "Global_active_power"]
    ].to_string(index=False)
)

# Compare median and upper percentiles
print("\nPercentile comparison:")
for name, series in [
    ("August", august["Energy_kWh"]),
    ("Rest", other["Energy_kWh"])
]:
    print(
        f"{name}: "
        f"Median={series.median():.3f}, "
        f"95th percentile={series.quantile(0.95):.3f}, "
        f"99th percentile={series.quantile(0.99):.3f}"
    )
