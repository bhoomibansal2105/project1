import redis
import json

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

data = r.get("instrumentid_to_name")

instrument_dict = json.loads(data)

print(instrument_dict)
