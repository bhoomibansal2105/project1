import pandas as pd

# Read source CSV
df = pd.read_csv("master_nse.csv")

# Remove everything after 'T' in expiry_date
df["expiry_date"] = (
    df["expiry_date"]
    .astype(str)
    .str.split("T")
    .str[0]
)



# Get first 3 unique expiry dates
first_3_expiries = sorted(df["expiry_date"].dropna().unique())[:3]

# Filter rows
df_clean = df[df["expiry_date"].isin(first_3_expiries)].copy()

# Save cleaned CSV
df_clean.to_csv("cleaned_instruments.csv", index=False)

# Create exchange_instrument -> instrument_name mapping
mapping_df = (
    df_clean[["exchange_instrument_id", "instrument_name"]]
    .drop_duplicates()
)

# Save mapping CSV
mapping_df.to_csv(
    "exchange_instrument_mapping.csv",
    index=False
)

print(f"Cleaned CSV rows: {len(df_clean)}")
print(f"Unique instruments: {len(mapping_df)}")
print("Saved:")
print(" - cleaned_instruments.csv")
print(" - exchange_instrument_mapping.csv")
