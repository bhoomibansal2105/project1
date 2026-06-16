import pandas as pd
import redis
import json

# ==========================================================
# Redis Connection
# ==========================================================
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# ==========================================================
# Read Master File
# ==========================================================
df = pd.read_csv(
    "master_nse_new.csv",
    low_memory=False
)

# Clean column names
df.columns = df.columns.str.strip()

# ==========================================================
# Common FO Filter
# ==========================================================
fo_df = df[
    df["exchange_segment_id"].isin(["NSEFO", "BSEFO"])
].copy()

# Clean symbol column
fo_df["expiry_symbol"] = (
    fo_df["expiry_symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Parse expiry dates
fo_df["expiry_date"] = pd.to_datetime(
    fo_df["expiry_date"],
    errors="coerce"
)

index_symbols = ["NIFTY", "BANKNIFTY", "SENSEX"]

# ==========================================================
# 1. INDEX EXPIRY DATES (Top 3 Expiries)
# ==========================================================
expiry_dict = {}

for symbol in index_symbols:
    expiry_dict[symbol] = (
        fo_df.loc[
            fo_df["expiry_symbol"] == symbol,
            "expiry_date"
        ]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .dt.strftime("%Y-%m-%d")
        .head(3)
        .tolist()
    )

# Store in Redis
r.set(
    "index_expiry_dates",
    json.dumps(expiry_dict)
)

print("Stored Redis Key: index_expiry_dates")
print(expiry_dict)

# ==========================================================
# Common Filter for Instrument Mappings
# ==========================================================
instrument_df = fo_df[
    (fo_df["expiry_symbol"].isin(index_symbols)) &
    (
        fo_df["expiry_series"]
        .astype(str)
        .str.strip()
        .str.upper() != "FUTIDX"
    )
].copy()

# ==========================================================
# 2. instrumentid_to_name (ALL EXPIRIES)
# ==========================================================
instrumentid_to_name = dict(
    zip(
        instrument_df["exchange_instrument_id"].astype(str),
        instrument_df["instrument name"].astype(str)
    )
)

r.set(
    "instrumentid_to_name",
    json.dumps(instrumentid_to_name)
)

print(
    f"\nStored Redis Key: instrumentid_to_name "
    f"({len(instrumentid_to_name)} records)"
)

# ==========================================================
# 3. instrumentname_to_id (ALL EXPIRIES)
# ==========================================================
instrumentname_to_id = dict(
    zip(
        instrument_df["instrument name"].astype(str),
        instrument_df["exchange_instrument_id"].astype(str)
    )
)

r.set(
    "instrumentname_to_id",
    json.dumps(instrumentname_to_id)
)

print(
    f"Stored Redis Key: instrumentname_to_id "
    f"({len(instrumentname_to_id)} records)"
)

# ==========================================================
# 4. instrument_mapping (TOP 3 EXPIRIES ONLY)
# ==========================================================

# Collect top 3 expiries across NIFTY/BANKNIFTY/SENSEX
top_3_expiries = sorted(
    {
        expiry
        for expiries in expiry_dict.values()
        for expiry in expiries
    }
)

# Filter only top 3 expiry instruments
cleaned_df = instrument_df[
    instrument_df["expiry_date"]
    .dt.strftime("%Y-%m-%d")
    .isin(top_3_expiries)
].copy()

# Save cleaned instruments CSV
cleaned_df.to_csv(
    "cleaned_instruments.csv",
    index=False
)

# Create mapping DataFrame
mapping_df = (
    cleaned_df[
        ["exchange_instrument_id", "instrument name"]
    ]
    .drop_duplicates()
)

# Save mapping CSV
mapping_df.to_csv(
    "exchange_instrument_mapping.csv",
    index=False
)

# Create Redis Mapping
instrument_mapping = dict(
    zip(
        mapping_df["exchange_instrument_id"].astype(str),
        mapping_df["instrument name"].astype(str)
    )
)

r.set(
    "instrument_mapping",
    json.dumps(instrument_mapping)
)

print(
    f"Stored Redis Key: instrument_mapping "
    f"({len(instrument_mapping)} records)"
)

# ==========================================================
# Verification
# ==========================================================
print("\n===== Verification =====")

print("\nindex_expiry_dates:")
print(json.loads(r.get("index_expiry_dates")))

print("\ninstrumentid_to_name count:")
print(len(json.loads(r.get("instrumentid_to_name"))))

print("\ninstrumentname_to_id count:")
print(len(json.loads(r.get("instrumentname_to_id"))))

print("\ninstrument_mapping count:")
print(len(json.loads(r.get("instrument_mapping"))))

print("\nGenerated Files:")
print(" - cleaned_instruments.csv")
print(" - exchange_instrument_mapping.csv")