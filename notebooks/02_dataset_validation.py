
import pandas as pd

file_path = "data/household_power_consumption_cleaned.csv"

df = pd.read_csv(file_path)

# 1. Dataset size
print("Dataset Shape:", df.shape)

# 2. Duplicate rows
print("\nDuplicate Rows:", df.duplicated().sum())

# 3. Convert Datetime column into datetime format
df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")

print("\nDatetime Data Type:", df["Datetime"].dtype)

# 4. Date range
print("\nStarting Date:", df["Datetime"].min())
print("Ending Date:", df["Datetime"].max())

# 5. Invalid datetime values
print("\nInvalid Datetime Values:", df["Datetime"].isna().sum())

# 6. Numeric columns summary
print("\nNumeric Columns Summary:")
print(df.describe().round(2))
