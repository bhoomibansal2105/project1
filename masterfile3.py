import pandas as pd
import redis
import msgspec
import json

# Connect to Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Read CSV
df = pd.read_csv(
    "master_nse_final.csv",
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

# Remove duplicate instrument names if present
filtered_df = filtered_df.drop_duplicates(subset=["instrument name"])

# Create dictionary:
# instrument_name -> exchange_segment_id
mapping = dict(
    zip(
        filtered_df["instrument name"].astype(str),
        filtered_df["exchange_instrument_id"].astype(str)
    )
)

# Convert to JSON
# json_data = json.dumps(mapping, indent=4)
json_data = msgspec.json.encode(mapping)

# Store in Redis as STRING
r.set("instrumentname_to_segment", json_data)

print(f"Stored {len(mapping)} records in Redis")

data = r.get("instrumentname_to_segment")

mapping = json.loads(data)

print(mapping)