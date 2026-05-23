import os
import csv
import random
from math import ceil, log2
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from Segment_tree_adt import (create_tree, build_max, build_min, build_sum, query_max, query_min, query_sum,get_mean, get_range, get_IQR,)
 
 
# ________________________________________________________________
#  1 – Fetch Stock Data
# ________________________________________________________________

def fetch_stock_data(ticker, csv_path):
    """
    Fetch 7-day, 1-min interval closing prices for ticker using yfinance library.
    Saves every row to csv_path and returns a list of dicts:
    [{"datetime": datetime_obj, "close": float}, ...]
 
    Time complexity: O(n)  -  each minute fetched and written once.
    """
 
    print(f"Fetching 1 week data for {ticker}")
 
    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=7) # current time - 7 days
 
    tkr = yf.Ticker(ticker) #using yfinance lib to and getting the wanted tickers data
    df  = tkr.history(start=start_dt, end=end_dt, interval="1m") #df is pandas dataframe that contains the data of the ticker for the past 7 days with 1 minute interval 
 
    if df.empty:
        raise ValueError(f"No data returned for {ticker}. Check the symbol and your internet connection.")
 
    # Change timezone to UTC 
    if df.index.tz is not None:
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    
    mydata = []
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["datetime", "open", "high", "low", "close", "volume"]) #Writes column names for the csv file
        for timestamp, row in df.iterrows():
            #appending data to csv
            dt_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") #converting timestamp to string format
            writer.writerow([
                dt_str,
                round(float(row["Open"]),  4),
                round(float(row["High"]),  4),
                round(float(row["Low"]),   4),
                round(float(row["Close"]), 4),
                int(row["Volume"]),
            ])
            #appending the data to the list of dicts
            mydata.append({"datetime": timestamp.to_pydatetime(), "close": float(row["Close"])})  
 
    print(f"{len(mydata)} rows saved to '{csv_path}'")
    return mydata
 
 
def load_stock_data(csv_path):
    """
    Load previously saved CSV back into the same list-of-dicts format.
    Time complexity: O(n)
    """
    rows = []
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append({
                "datetime": datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S"),
                "close":    float(r["close"]),
            })
    print(f"Loaded {len(rows)} rows from '{csv_path}'")
    return rows

  
# 
# ________________________________________________________________
#  2 – SEGMENT TREE CONSTRUCTION
# ________________________________________________________________
 
def build_trees(close_prices):
    """
    Allocate three segment trees of size 4n (as per project spec) and
    build max, min, and sum trees over close_prices.
  
    Time complexity: O(3n) -> O(n) total.
    Memory: O(3n) -> O(n) total.
    """
    n = len(close_prices)
    print(f"Building segment trees for {n} nodes")
 
    # All three trees share the same skeleton size
    max_tree = create_tree(close_prices)
    min_tree = create_tree(close_prices)
    sum_tree = create_tree(close_prices)
 
    build_max(0, 0, n - 1, max_tree, close_prices)
    build_min(0, 0, n - 1, min_tree, close_prices)
    build_sum(0, 0, n - 1, sum_tree, close_prices)
 
    print("Trees built.")
    return max_tree, min_tree, sum_tree
 
 
# ________________________________________________________________
#  SECTION 3 – DATETIME -> INDEX CONVERSION
# ________________________________________________________________
 
# All formats we'll try to parse, from most to least common
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%m/%d/%Y %H:%M",
    "%Y/%m/%d %H:%M",
    "%d %b %Y %H:%M",    # e.g. 21 Apr 2025 09:30
    "%d %B %Y %H:%M",    # e.g. 21 April 2025 09:30
]
 
def parse_datetime(dt_str):
    """Try several common formats; raise ValueError if none match."""
    dt_str = dt_str.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse '{dt_str}'.\n"
        f"  Accepted formats: {', '.join(DATETIME_FORMATS)}"
    )
 
 
def datetime_to_index(target,timestamps):
    """
    Map a target datetime to the nearest index in timestamps using
    binary search.  Falls back to nearest neighbour when no exact match
    (e.g. the user enters a time when the market was closed).
 
    Time complexity: O(log n) [Binary Search]
    """

    lo, hi = 0, len(timestamps) - 1
 
    while lo <= hi:
        mid = (lo + hi) // 2
        if timestamps[mid] == target:
            return mid
        elif timestamps[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
 
    # lo is the insertion point. pick the closer neighbour
    if lo == 0:
        return 0
    if lo >= len(timestamps):
        return len(timestamps) - 1
    
    #Getting the closest index to the target datetime by comparing the two neighbours where the crossover of lo and high happened in binary search
    before = abs(timestamps[lo - 1] - target)
    after  = abs(timestamps[lo]     - target)
    if before <= after:
        return lo - 1
    else:
        return lo
 
 
# ________________________________________________________________
#  SECTION 4 – INTERACTIVE QUERY LOOP
# ________________________________________________________________
 
QUERY_MENU = """
   _____________________________________________
  |                                             |
  │          SEGMENT TREE QUERY MENU            │
  |_____________________________________________|
  │  1  Max price in range        O(log n)      │
  │  2  Min price in range        O(log n)      │
  │  3  Sum of prices in range    O(log n)      │
  │  4  Mean price in range       O(log n)      │
  │  5  Price range (max - min)   O(log n)      │
  │  6  IQR of prices             O(n log n)    │
  │  7  Change ticker / reload data             │
  │  Q  Quit                                    │
  |_____________________________________________| 
"""
 
def get_query_range(timestamps):
    """
    Ask the user for start and end datetimes.
    Returns (l, r) as segment-tree array indexes.
    """

    print("Enter a datetime in any of these formats:")
    print("YYYY-MM-DD HH:MM   |   DD/MM/YYYY HH:MM   |")
 
    start_str = input("Start datetime: ").strip()
    end_str = input("End datetime: ").strip()
 
    start_dt = parse_datetime(start_str)
    end_dt = parse_datetime(end_str)
 
    if end_dt < start_dt:
        print("[WARNING] End is before start — swapping them.")
        start_dt, end_dt = end_dt, start_dt
 
    l = datetime_to_index(start_dt, timestamps)
    r = datetime_to_index(end_dt,   timestamps)
 
    if l > r:
        l, r = r, l
 
    print(f"Actual range:  {timestamps[l]}  ->  {timestamps[r]}")
    print(f"Data points in range: {r - l + 1}")
    return l, r
 
 
def query_loop(close_prices, timestamps, max_tree, min_tree, sum_tree):
    """Interactive loop: allows user to query the segment trees repeatedly."""
    n = len(close_prices)
 
    while True:
        print(QUERY_MENU)
        choice = input("Select option: ").strip().lower()
 
        if choice == "q":
            print("Goodbye!")
            break
 
        if choice == "7":
            return "RELOAD"           # signal caller to restart with new ticker
 
        if choice not in ("1", "2", "3", "4", "5", "6"):
            print("Invalid choice — please enter 1-7, or q.")
            continue
 
        try:
            l, r = get_query_range(timestamps)
        except ValueError as e:
            print(f"[ERROR] {e}")
            continue
 
        # ── dispatch to appropriate segment-tree function ─────────────────
        if choice == "1":
            result = query_max(0, 0, n - 1, l, r, max_tree)
            print()
            print(f">>> MAX price in range: ${result:.4f}")
 
        elif choice == "2":
            result = query_min(0, 0, n - 1, l, r, min_tree)
            print()
            print(f">>> MIN price in range: ${result:.4f}")
 
        elif choice == "3":
            result = query_sum(0, 0, n - 1, l, r, sum_tree)
            print()
            print(f">>> SUM of prices: ${result:.4f}")
 
        elif choice == "4":
            result = get_mean(0, 0, n - 1, l, r, sum_tree)
            print()
            print(f">>> MEAN price: ${result:.4f}")
 
        elif choice == "5":
            result = get_range(0, 0, n - 1, l, r, max_tree, min_tree)
            print()
            print(f">>> PRICE RANGE (max-min): ${result:.4f}")
 
        elif choice == "6":
            result = get_IQR(close_prices, l, r)
            print()
            print(f">>> IQR: ${result:.4f}")
 
        input("\n  Press Enter to continue ...")
 
    return "QUIT"
 
 
# ________________________________________________________________
#  SECTION 5 – MAIN ENTRY POINT
# ________________________________________________________________
 
def main():
    print("=" * 57)
    print(" Stock Analysis using Segment Trees")
    print("|Ali Hani| & |Aaisha Siddiqui|")
    print("=" * 57)
 
    while True:
        ticker = input("\nEnter stock ticker (e.g. AAPL, MSFT, TSLA): ").strip().upper()
        if not ticker:
            print("Ticker cannot be empty.")
            continue
        time_now = datetime.now().strftime("%Y-%m-%d %H_%M")
        csv_path = f"{ticker}__{time_now}.csv"
 
        # ── decide data source ────────────────────────────────────────────
        existing_csv = None
        candidates = [f for f in os.listdir('.') if f.startswith(f"{ticker}__")]
        if candidates:
            existing_csv = max(candidates, key=os.path.getmtime)
            print(f"\n  Found existing CSV: '{existing_csv}'")
            choice = input(
                "  [L]oad existing  /  [F]etch fresh from Yahoo Finance"
            ).strip().upper()
        else:
            choice = "F"
 
        rows = None
        try:
            if choice == "L" and existing_csv:
                rows = load_stock_data(existing_csv)
            else:
                rows = fetch_stock_data(ticker, csv_path)
        except Exception as e:
            print(f"\n  [ERROR] {e}")
            continue
 
        if not rows:
            print("[ERROR] No data available. Please try again.")
            continue
 
        # ── extract parallel arrays ───────────────────────────────────────
        timestamps   = [r["datetime"] for r in rows]   # list[datetime]
        close_prices = [r["close"]    for r in rows]   # list[float]
        print()
        print(f"  Ticker     : {ticker}")
        print(f"  Data range   : {timestamps[0]}  ->  {timestamps[-1]}")
        print(f"  Total rows   : {len(rows)}")
        print(f"  Price range  : ${min(close_prices):.4f} | ${max(close_prices):.4f}")
 
        # ── build all three trees ─────────────────────────────────────────
        max_tree, min_tree, sum_tree = build_trees(close_prices)
 
        # ── enter query loop ──────────────────────────────────────────────
        signal = query_loop(close_prices, timestamps, max_tree, min_tree, sum_tree)
 
        if signal == "QUIT":
            break
        # signal == "RELOAD" -> loop back to ticker prompt


if __name__ == "__main__":
    main()