import pandas as pd
import redis
import json
import msgspec

# Connect to Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Read CSV
df = pd.read_csv(
    "master_nse_new.csv",
    low_memory=False
)

# Clean column names
df.columns = df.columns.str.strip()

# Apply filters
filtered_df = df[
    (df["exchange_segment_id"].isin(["NSEFO", "BSEFO"])) &
    (df["expiry_symbol"].isin(["NIFTY", "BANKNIFTY", "SENSEX"])) &
    (df["expiry_series"].astype(str).str.strip().str.upper() != "FUTIDX")
].copy()

# Create instrument_id -> instrument_name dictionary
instrument_dict = dict(
    zip(
        filtered_df["exchange_instrument_id"].astype(str),
        filtered_df["instrument name"].astype(str)
    )
)

# Convert dictionary to JSON string
json_data = json.dumps(instrument_dict)
# json_data = msgspec.json.encode(instrument_dict)

# Store as a Redis STRING
r.set("instrumentid_to_name", json_data)

print(f"Stored {len(instrument_dict)} records in Redis")

# Retrieve and verify
data = r.get("instrumentid_to_name")

instrument_dict = json.loads(data)

print(instrument_dict)
