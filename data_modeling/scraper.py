import os
import time
import ccxt
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone, timedelta

# === CONFIG ===
START_DATE = '2020-01-01'
INTERVAL = '1m'
BUCKET = 'crypto.kline.data'
LOCAL_TMP_DIR = './data'
SYMBOL_DIR = 'symbols.txt'

# AWS client
# s3 = boto3.client('s3')
exchange = ccxt.binance()

# === HELPERS ===
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_symbols(loc):
    with open(loc, 'r') as f:
        symbols = f.readlines()
    return [i.strip() for i in symbols if len(i.strip()) > 0]

# def s3_file_exists(symbol, day):
#     normalized_symbol = symbol.replace("/", "-")
#     s3_key = f"{exchange.id}/{INTERVAL}/{normalized_symbol}/{day}.parquet"
#     try:
#         s3.head_object(Bucket=BUCKET, Key=s3_key)
#         return True
#     except s3.exceptions.ClientError as e:
#         if e.response['Error']['Code'] == "404":
#             return False
#         raise

def fetch_day_ohlcv(symbol, since_ts, until_ts):
    all_candles = []
    ts = since_ts
    while ts < until_ts:
        try:
            candles = exchange.fetch_ohlcv(symbol, timeframe=INTERVAL, since=ts, limit=1000)
            if not candles:
                break
            for c in candles:
                if c[0] >= until_ts:
                    break
                all_candles.append(c)
            ts = candles[-1][0] + 60_000
            time.sleep(0.25)
        except Exception as e:
            print(f"[Error] {symbol} @ {datetime.fromtimestamp(ts / 1000, timezone.utc)} : {e}")
            time.sleep(3)
    return all_candles

def save_daily_parquet_to_s3(symbol, day, candles):
    if not candles:
        print(f"[⚠️ Empty] No data for {symbol} on {day}")
        return

    normalized_symbol = symbol.replace("/", "-")
    s3_key = f"{exchange.id}/{INTERVAL}/{normalized_symbol}/{day}.parquet"
    local_path = os.path.join(LOCAL_TMP_DIR, s3_key.replace("/", "_"))
    ensure_dir(os.path.dirname(local_path))

    table = pa.Table.from_arrays(
        [
            pa.array([row[0] for row in candles], type=pa.int64()),     # timestamp
            pa.array([row[1] for row in candles], type=pa.float64()),   # open
            pa.array([row[2] for row in candles], type=pa.float64()),   # high
            pa.array([row[3] for row in candles], type=pa.float64()),   # low
            pa.array([row[4] for row in candles], type=pa.float64()),   # close
            pa.array([row[5] for row in candles], type=pa.float64()),   # volume
            pa.array([symbol] * len(candles)),                          # symbol
            pa.array([exchange.id] * len(candles)),                     # exchange
            pa.array([INTERVAL] * len(candles)),                        # interval
        ],
        names=["timestamp", "open", "high", "low", "close", "volume", "symbol", "exchange", "interval"]
    )

    pq.write_table(table, local_path, compression='snappy')
    # s3.upload_file(local_path, BUCKET, s3_key)
    # print(f"[S3 ✅] {symbol} {day} → {s3_key}")

# === MAIN ===
def main():
    ensure_dir(LOCAL_TMP_DIR)
    symbols = read_symbols(SYMBOL_DIR)
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    start_date = datetime.strptime(START_DATE, '%Y-%m-%d').date()
    end_date = datetime.now(timezone.utc).date()

    for symbol in symbols:
        print(f"==> Processing {symbol}")
        current_date = end_date
        while current_date >= start_date:
            day_str = current_date.isoformat()
            # if s3_file_exists(symbol, day_str):
            #     print(f"[🛑 Skip] {symbol} {day_str} already exists in S3")
            #     current_date -= timedelta(days=1)
            #     continue
            since_ts = int(datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
            until_ts = since_ts + 24 * 60 * 60 * 1000
            print(f"[📥 Fetching] {symbol} {day_str}")
            candles = fetch_day_ohlcv(symbol, since_ts, until_ts)
            save_daily_parquet_to_s3(symbol, day_str, candles)
            current_date -= timedelta(days=1)

if __name__ == "__main__":
    main()
