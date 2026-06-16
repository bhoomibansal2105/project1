import redis
import json
from datetime import datetime
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)

# Redis containing live feed
r2 = redis.Redis(
    host="192.168.161.169",
    port=6380,
    db=0
)

#functions
def get_redis_dict(redis_key):
    """
    Read JSON dictionary from Redis
    """
    value = r.get(redis_key)
    
    if value is None:
        return None

    value = value.decode("utf-8")

    return json.loads(value)


def get_redisvalue(redis_key, lookup_key):
    """
    Lookup value inside Redis JSON dictionary
    """
    data = get_redis_dict(redis_key)

    if data is None:
        return None

    return data.get(lookup_key)


def parse_fetch_values(redis_key):
    """
    Parse feed data stored as:
    key=value|key=value|...
    """

    value = r2.get(redis_key)

    if value is None:
        raise KeyError(f"Redis key '{redis_key}' not found")

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    parsed = {}

    for item in value.split('|'):

        if '=' not in item:
            continue

        key, val = item.split('=', 1)

        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass

        parsed[key] = val

    return parsed

def convert_date(date_str):
    """
    Convert YYYY-MM-DD to DDMMMYYYY
    Example:
    2026-06-16 → 16JUN2026
    """
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%d%b%Y").upper()


def calculate_atm_straddle():
    # STEP 1 : Spot Price
    spot_redis_key = "1_26000"

    spot_data = parse_fetch_values(spot_redis_key)

    spot = spot_data['8'] / 100

    atm = int((spot + 25) / 50) * 50

    print("\n========== SPOT DETAILS ==========")
    print("Spot Redis Key :", spot_redis_key)
    print("Spot Price     :", spot)
    print("ATM Strike     :", atm)

    # STEP 2 : User Inputs
    expiry_symbol = input(
        "\nEnter expiry symbol (NIFTY/BANKNIFTY/SENSEX): "
    ).upper()

    expiry_date = input(
        "Enter expiry date (YYYY-MM-DD): "
    )

    expiry_date = convert_date(expiry_date)

    # STEP 3 : Lookup Keys
    ce_lookup_key = " ".join([
        expiry_symbol,
        expiry_date,
        "CE",
        str(atm)
    ])

    pe_lookup_key = " ".join([
        expiry_symbol,
        expiry_date,
        "PE",
        str(atm)
    ])

    print("\n========== LOOKUP KEYS ==========")
    print("CE Lookup Key :", ce_lookup_key)
    print("PE Lookup Key :", pe_lookup_key)

    # STEP 4 : Instrument IDs
    ce_instrument_id = get_redisvalue(
        "instrumentname_to_id",
        ce_lookup_key
    )

    pe_instrument_id = get_redisvalue(
        "instrumentname_to_id",
        pe_lookup_key
    )

    if ce_instrument_id is None:
        raise KeyError(f"CE Instrument not found: {ce_lookup_key}")

    if pe_instrument_id is None:
        raise KeyError(f"PE Instrument not found: {pe_lookup_key}")

    print("\n========== INSTRUMENT IDS ==========")
    print("CE Instrument ID :", ce_instrument_id)
    print("PE Instrument ID :", pe_instrument_id)

    # STEP 5 : Segment Mapping
    segment_map = {
        "NIFTY": 2,
        "BANKNIFTY": 2,
        "SENSEX": 4
    }

    segment_id = segment_map.get(expiry_symbol)

    if segment_id is None:
        raise ValueError(
            f"Unsupported symbol: {expiry_symbol}"
        )

    # STEP 6 : CE Price
    ce_redis_key = f"{segment_id}_{ce_instrument_id}"

    ce_data = parse_fetch_values(ce_redis_key)

    ce_price = ce_data['8'] / 100

    print("\n========== CALL OPTION ==========")
    print("Redis Key :", ce_redis_key)
    print("Field 8   :", ce_data['8'])
    print("CE Price  :", ce_price)

    # STEP 7 : PE Price
    pe_redis_key = f"{segment_id}_{pe_instrument_id}"

    pe_data = parse_fetch_values(pe_redis_key)

    pe_price = pe_data['8'] / 100

    print("\n========== PUT OPTION ==========")
    print("Redis Key :", pe_redis_key)
    print("Field 8   :", pe_data['8'])
    print("PE Price  :", pe_price)

    # STEP 8 : Straddle
    straddle = ce_price + pe_price

    print("\n========== ATM STRADDLE ==========")
    print("Spot Price   :", spot)
    print("ATM Strike   :", atm)
    print("Call Price   :", ce_price)
    print("Put Price    :", pe_price)
    print("Straddle     :", straddle)

    return straddle
calculate_atm_straddle()
