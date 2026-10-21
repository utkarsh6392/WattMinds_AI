
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/hourly_energy_data.csv")
df["Hour"] = pd.to_datetime(df["Hour"])

# Compare July, August and September
df["Year_Month"] = df["Hour"].dt.to_period("M").astype(str)

months = ["2008-07", "2008-08", "2008-09"]
data = df[df["Year_Month"].isin(months)].copy()

# Check energy and power values together
print("\nMONTHLY COLUMN COMPARISON")
print("=" * 70)

monthly = data.groupby("Year_Month").agg(
    Average_Energy_kWh=("Energy_kWh", "mean"),
    Average_Global_Active_Power=("Global_active_power", "mean"),
    Average_Voltage=("Voltage", "mean"),
    Average_Global_Intensity=("Global_intensity", "mean"),
    Average_Submeter_1=("Sub_metering_1_kWh", "mean"),
    Average_Submeter_2=("Sub_metering_2_kWh", "mean"),
    Average_Submeter_3=("Sub_metering_3_kWh", "mean")
).round(3)

print(monthly)

# Distribution of hourly energy
plt.figure(figsize=(10, 6))

for month in months:
    values = data.loc[
        data["Year_Month"] == month, "Energy_kWh"
    ]
    plt.hist(values, bins=40, alpha=0.5, label=month)

plt.title("Hourly Energy Distribution: July–September 2008")
plt.xlabel("Hourly Energy (kWh)")
plt.ylabel("Number of Hours")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig(
    "outputs/hourly_energy_distribution_comparison.png",
    dpi=300
)
plt.show()

print("\nChart saved successfully.")
