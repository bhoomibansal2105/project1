import redis
import json

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

data = r.get("instrumentname_to_segment")

mapping = json.loads(data)

print(mapping)