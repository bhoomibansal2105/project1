import pandas as pd

# Read CSV
df = pd.read_csv("master_nse_final.csv")

# Remove data after 'T' in expiry_date column
df["expiry_date"] = df["expiry_date"].astype(str).str.split("T").str[0]

# Get first 3 unique expiry dates
first_3_expiries = sorted(df["expiry_date"].dropna().unique())[:3]

# Filter dataframe for only those 3 expiry dates
df_filtered = df[df["expiry_date"].isin(first_3_expiries)]

# Create exchange_instrument -> instrument_name mapping
instrument_mapping = dict(
    zip(
        df_filtered["exchange_instrument_id"],
        df_filtered["instrument name"]
    )
)

print("First 3 Expiry Dates:")
print(first_3_expiries)

print("\nInstrument Mapping:")
print(instrument_mapping)
