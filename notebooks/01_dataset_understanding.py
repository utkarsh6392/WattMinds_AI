import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

file_path = "data/household_power_consumption_cleaned.csv"

df = pd.read_csv(file_path)

print("Dataset Shape:", df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

print("\nFirst 5 Rows:")
print(df.head())

print("\nData Types:")
print(df.dtypes)

print("\nMissing Values:")
print(df.isnull().sum())