import redis
import json
import time
from datetime import datetime

# ============================================================
# REDIS CONNECTIONS
# ============================================================

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)

r2 = redis.Redis(
    host="192.168.161.169",
    port=6380,
    db=0
)

# ============================================================
# HELPERS
# ============================================================

def get_redis_dict(redis_key):
    value = r.get(redis_key)

    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    return json.loads(value)


def get_redisvalue(redis_key, lookup_key):
    data = get_redis_dict(redis_key)
    if data is None:
        return None
    return data.get(lookup_key)


def parse_fetch_values(redis_key):
    value = r2.get(redis_key)

    if value is None:
        raise KeyError(f"Redis key '{redis_key}' not found")

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    parsed = {}

    for item in value.split("|"):
        if "=" not in item:
            continue

        k, v = item.split("=", 1)

        try:
            v = int(v)
        except:
            try:
                v = float(v)
            except:
                pass

        parsed[k] = v

    return parsed


def convert_date(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%d%b%Y").upper()


def get_spot(segment,token):
    return parse_fetch_values(f"{segment}_{token}")["8"] / 100


def get_atm(spot):
    return int((spot + 25) / 50) * 50


def get_option_prices(symbol, expiry, atm):

    ce_key = f"{symbol} {expiry} CE {atm}"
    pe_key = f"{symbol} {expiry} PE {atm}"

    ce_id = get_redisvalue("instrumentname_to_id", ce_key)
    pe_id = get_redisvalue("instrumentname_to_id", pe_key)

    if ce_id is None or pe_id is None:
        return None, None

    segment_map = {
        "NIFTY": 2,
        "BANKNIFTY": 2,
        "SENSEX": 4
    }

    seg = segment_map.get(symbol)
    if seg is None:
        return None, None

    try:
        ce_data = parse_fetch_values(f"{seg}_{ce_id}")
        pe_data = parse_fetch_values(f"{seg}_{pe_id}")

        ce_price = ce_data["8"] / 100
        pe_price = pe_data["8"] / 100

        return ce_price, pe_price

    except:
        return None, None


# ============================================================
# MAIN STRATEGY
# ============================================================
spot_token = {"NIFTY": "26000", "BANKNIFTY": "26009", "SENSEX": "19000"}
def monitor_strategy(symbol, expiry, spot_move, straddle_move):

    symbol = symbol.upper()
    expiry = convert_date(expiry)
    segment = 1 if symbol in ["NIFTY", "BANKNIFTY"] else 3

    print("\nWaiting for initial data...")

    initial_ce = initial_pe = None
    last_ce = last_pe = None

    while True:
        try:
            initial_spot = get_spot(segment, spot_token.get(symbol))
            initial_atm = get_atm(initial_spot)

            ce, pe = get_option_prices(symbol, expiry, initial_atm)

            if ce is None or pe is None:
                time.sleep(1)
                continue

            initial_ce, initial_pe = ce, pe
            last_ce, last_pe = ce, pe

            initial_straddle = ce + pe
            break

        except Exception:
            time.sleep(1)

    upper_spot = initial_spot + spot_move
    lower_spot = initial_spot - spot_move

    upper_straddle = initial_straddle + straddle_move
    lower_straddle = initial_straddle - straddle_move

    print("\n" + "=" * 60)
    print("INITIAL VALUES")
    print("=" * 60)
    print(f"Initial Spot     : {initial_spot:.2f}")
    print(f"Initial ATM      : {initial_atm}")
    print(f"Initial CE       : {initial_ce:.2f}")
    print(f"Initial PE       : {initial_pe:.2f}")
    print(f"Initial Straddle : {initial_straddle:.2f}")
    print(f"Upper Spot       : {upper_spot:.2f}")
    print(f"Lower Spot       : {lower_spot:.2f}")
    print(f"Upper Straddle   : {upper_straddle:.2f}")
    print(f"Lower Straddle   : {lower_straddle:.2f}")
    print("=" * 60)
    print("Monitoring Started...")
    print("=" * 60)

    exit_reason = ""
    iteration = 0

    while True:

        try:
            iteration += 1

            spot = get_spot(segment, spot_token.get(symbol))
            atm = get_atm(spot)

            ce, pe = get_option_prices(symbol, expiry, atm)

            if ce is not None and pe is not None:
                last_ce, last_pe = ce, pe

            current_straddle = last_ce + last_pe

            # heartbeat
            if iteration % 60 == 0:
                print(f"Still monitoring... {datetime.now().strftime('%H:%M:%S')}")

            # SPOT EXIT
            if spot >= upper_spot:
                exit_reason = "SPOT +MOVE"
                break

            if spot <= lower_spot:
                exit_reason = "SPOT -MOVE"
                break

            # STRADDLE EXIT
            if current_straddle >= upper_straddle:
                exit_reason = "STRADDLE +MOVE"
                break

            if current_straddle <= lower_straddle:
                exit_reason = "STRADDLE -MOVE"
                break

        except Exception:
            pass

        time.sleep(1)

    print("\n" + "=" * 60)
    print("STRATEGY EXIT")
    print("=" * 60)
    print(f"Reason        : {exit_reason}")
    print(f"Final Spot    : {spot:.2f}")
    print(f"Final ATM     : {atm}")
    print(f"Final CE      : {last_ce:.2f}")
    print(f"Final PE      : {last_pe:.2f}")
    print(f"Final Straddle: {current_straddle:.2f}")
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    symbol = input("Enter expiry symbol (NIFTY/BANKNIFTY/SENSEX): ")
    expiry = input("Enter expiry date (YYYY-MM-DD): ")

    spot_move = float(input("Enter Spot movement points: "))
    straddle_move = float(input("Enter Straddle movement points: "))

    monitor_strategy(symbol, expiry, spot_move, straddle_move)
    