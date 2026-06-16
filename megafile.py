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
# Common Filters
# ==========================================================

# Only FO segments
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

# ==========================================================
# 1. INDEX EXPIRY DATES
# ==========================================================
# Same logic as your standalone script

expiry_df = fo_df.copy()

expiry_df["expiry_date"] = pd.to_datetime(
    expiry_df["expiry_date"],
    errors="coerce"
)

expiry_dict = {}

for symbol in ["NIFTY", "BANKNIFTY", "SENSEX"]:
    expiry_dict[symbol] = (
        expiry_df.loc[
            expiry_df["expiry_symbol"] == symbol,
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
# 2. INSTRUMENT ID -> INSTRUMENT NAME
# ==========================================================
# EXACTLY same filter as standalone script

instrument_df = fo_df[
    (fo_df["expiry_symbol"].isin(["NIFTY", "BANKNIFTY", "SENSEX"])) &
    (
        fo_df["expiry_series"]
        .astype(str)
        .str.strip()
        .str.upper() != "FUTIDX"
    )
    
].copy()

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
# 3. INSTRUMENT NAME -> INSTRUMENT ID
# ==========================================================
# EXACTLY same logic as standalone script

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
# VERIFICATION
# ==========================================================

print("\n===== Verification =====")

# Expiry Dates
expiry_data = json.loads(r.get("index_expiry_dates"))
print("\nindex_expiry_dates:")
print(expiry_data)

# Instrument ID -> Name
id_to_name = json.loads(r.get("instrumentid_to_name"))
print("\ninstrumentid_to_name records:", len(id_to_name))
print("Sample:")
print(dict(list(id_to_name.items())[:5]))

# Instrument Name -> ID
name_to_id = json.loads(r.get("instrumentname_to_id"))
print("\ninstrumentname_to_id records:", len(name_to_id))
print("Sample:")
print(dict(list(name_to_id.items())[:5]))
