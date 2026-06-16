import pandas as pd
import redis
import json

# Connect to Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Read CSV
df = pd.read_csv("master_nse_new.csv", low_memory=False)

# Clean column names
df.columns = df.columns.str.strip()

# Filter only FO segments
df = df[df["exchange_segment_id"].isin(["NSEFO", "BSEFO"])].copy()

# Clean symbols
df["expiry_symbol"] = (
    df["expiry_symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Parse expiry dates
df["expiry_date"] = pd.to_datetime(
    df["expiry_date"],
    errors="coerce"
)

expiry_dict = {}

for symbol in ["NIFTY", "BANKNIFTY", "SENSEX"]:
    expiry_dict[symbol] = (
        df.loc[df["expiry_symbol"] == symbol, "expiry_date"]
        .dropna()
        .drop_duplicates()
        .sort_values()           # earliest upcoming expiries
        .dt.strftime("%Y-%m-%d")
        .head(3)
        .tolist()
    )

# Convert dictionary to JSON
expiry_json = json.dumps(expiry_dict)

# Store in Redis as a STRING
redis_key = "index_expiry_dates"
r.set(redis_key, expiry_json)

print(f"Stored in Redis under key: {redis_key}")
print(expiry_json)

# Verify by reading back from Redis
data = r.get(redis_key)

if data:
    expiry_dict_from_redis = json.loads(data)
    print("\nRetrieved from Redis:")
    print(expiry_dict_from_redis)
    
