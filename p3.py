import msgspec
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Get bytes from Redis
data = r.get("instrument_mapping")

# Decode back to dictionary
instrument_dict = msgspec.json.decode(data)

print(instrument_dict)

# Encode
encoded_data = msgspec.msgpack.encode(instrument_dict)

# Store
r.set("instrument_mapping", encoded_data)

# Retrieve
data = r.get("instrument_mapping")

# Decode
instrument_dict = msgspec.msgpack.decode(data)
