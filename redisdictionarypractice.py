
import redis 

r = redis.Redis(
    host="192.168.161.169",  
    port=6379,
    db=0
)

def parse_fetch_values(*keys):
    result = {}

    for redis_key in keys:
        value = r.get(redis_key)

        if value is None:
            result[redis_key] = None
            continue

        # Redis returns bytes by default
        if isinstance(value, bytes):
            value = value.decode("utf-8")

        parsed = {}

        for item in value.split('|'):
            key, val = item.split('=', 1)

            if val.isdigit():
                val = int(val)

            parsed[key] = val

        result[redis_key] = parsed

    return result



instrument_id=int(input("enter instrument id: "))
segment_id=int(input("enter segment id: "))
data = parse_fetch_values("1_26000", "1_26009", "3_19000")
print(data)
