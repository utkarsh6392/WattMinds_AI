
import pandas as pd
import numpy as np

df = pd.read_csv("data/hourly_energy_data.csv")
df["Hour"] = pd.to_datetime(df["Hour"])

# Validate the relationship between hourly power sum and energy
df["Calculated_Energy_kWh"] = df["Global_active_power"] / 60

df["Energy_Difference"] = (
    df["Energy_kWh"] - df["Calculated_Energy_kWh"]
).abs()

print("\nENERGY FORMULA VALIDATION")
print("=" * 60)

print("Maximum absolute difference:",
      df["Energy_Difference"].max())

print("Average absolute difference:",
      df["Energy_Difference"].mean())

print("\nSample rows:")
print(
    df[
        ["Hour", "Global_active_power",
         "Energy_kWh", "Calculated_Energy_kWh"]
    ].head(10).to_string(index=False)
)

# Monthly validation
df["Year_Month"] = df["Hour"].dt.to_period("M").astype(str)

monthly = df.groupby("Year_Month").agg(
    Average_Stored_Energy=("Energy_kWh", "mean"),
    Average_Recalculated_Energy=("Calculated_Energy_kWh", "mean")
).round(4)

print("\nMONTHLY VALIDATION")
print(monthly.loc[["2008-07", "2008-08", "2008-09"]])
