from pathlib import Path

import pandas as pd

# Project root is the parent of the src folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "cloud_billing.csv"

df = pd.read_csv(DATA_PATH)

required_columns = [
    "date",
    "provider",
    "service",
    "region",
    "resource_id",
    "usage_quantity",
    "cost",
    "currency",
]

# 1. Check required columns
missing_columns = set(required_columns) - set(df.columns)
assert not missing_columns, f"Missing columns: {missing_columns}"

# 2. Parse dates and numeric fields
df["date"] = pd.to_datetime(df["date"], errors="raise")
df["usage_quantity"] = pd.to_numeric(
    df["usage_quantity"], errors="raise"
)
df["cost"] = pd.to_numeric(df["cost"], errors="raise")

# 3. Validate values
assert df["date"].notna().all(), "Missing dates found"
assert df["provider"].isin(["AWS", "Azure", "GCP"]).all()
assert df["cost"].notna().all(), "Missing costs found"
assert (df["cost"] >= 0).all(), "Negative costs found"
assert (df["usage_quantity"] >= 0).all()

print("Dataset validation passed!")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Date range: {df['date'].min().date()} to "
      f"{df['date'].max().date()}")

print("\nRecords by provider:")
print(df.groupby("provider").size())

print("\nTotal cost by provider (INR):")
print(df.groupby("provider")["cost"].sum())

print(f"\nTotal recorded cost: ₹{df['cost'].sum():,.2f}")


# Additional data quality checks
assert not df[required_columns].isna().any().any(), (
    "Missing values found in required columns"
)

assert not df.duplicated().any(), "Duplicate rows found"

assert set(df["provider"].unique()) == {
    "AWS", "Azure", "GCP"
}, "Unexpected provider set"

print("Missing-value check: passed")
print("Duplicate-row check: passed")
print("Provider check: passed")
