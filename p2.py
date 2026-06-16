import pandas as pd
import msgspec
import redis

# Connect to Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True  # Important: store raw bytes
)

# Read CSV
df = pd.read_csv("cleaned_instruments.csv")

# Create dictionary
instrument_dict = dict(
    zip(
        df["exchange_instrument_id"].astype(str),
        df["instrument_name"]
    )
)

# Encode using msgspec JSON
encoded_data = msgspec.json.encode(instrument_dict)

# Store in Redis
r.set("instrument_mapping", encoded_data)

print("Successfully stored in Redis")
