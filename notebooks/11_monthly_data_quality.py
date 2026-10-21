
import pandas as pd

# Step 1: Load hourly dataset
file_path = "data/hourly_energy_data.csv"

df = pd.read_csv(file_path)

# Step 2: Convert Hour column to datetime
df["Hour"] = pd.to_datetime(df["Hour"])

# Step 3: Create Year-Month column
df["Year_Month"] = df["Hour"].dt.to_period("M")

# Step 4: Monthly data quality and consumption analysis
monthly_quality = df.groupby("Year_Month").agg(
    Available_Hours=("Hour", "count"),
    First_Reading=("Hour", "min"),
    Last_Reading=("Hour", "max"),
    Average_Energy_kWh=("Energy_kWh", "mean"),
    Total_Energy_kWh=("Energy_kWh", "sum")
)

# Step 5: Calculate expected hours in each calendar month
monthly_quality["Expected_Hours"] = [
    pd.Period(month, freq="M").days_in_month * 24
    for month in monthly_quality.index
]

# Step 6: Calculate monthly data coverage percentage
monthly_quality["Coverage_Percent"] = (
    monthly_quality["Available_Hours"]
    / monthly_quality["Expected_Hours"]
    * 100
)

# Step 7: Display complete monthly report
print("\nMONTHLY DATA QUALITY REPORT")
print("=" * 90)

print(
    monthly_quality.round(
        {
            "Average_Energy_kWh": 3,
            "Total_Energy_kWh": 3,
            "Coverage_Percent": 3
        }
    ).to_string()
)

# Step 8: Display August 2008 details
print("\n\nAUGUST 2008 DETAILS")
print("=" * 40)

august_data = monthly_quality.loc["2008-08"]

print("Available Hours:", august_data["Available_Hours"])
print("Expected Hours:", august_data["Expected_Hours"])
print("First Reading:", august_data["First_Reading"])
print("Last Reading:", august_data["Last_Reading"])
print(
    "Average Energy (kWh):",
    round(august_data["Average_Energy_kWh"], 3)
)
print(
    "Total Energy (kWh):",
    round(august_data["Total_Energy_kWh"], 3)
)
print(
    "Coverage (%):",
    round(august_data["Coverage_Percent"], 3)
)

# Step 9: Save the monthly report
output_path = "outputs/monthly_data_quality_report.csv"

monthly_quality.to_csv(output_path)

print("\nMonthly report saved to:", output_path)
