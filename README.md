# 📈 StockAnalysis — Range Analytics using Segment trees

> **DSA Project** by **Ali Hani**· *Prof. Nadia Nasir, L3*

A command-line Python application that fetches real-time stock data and performs lightning-fast range-based analytics using **Segment Trees** — turning O(n) brute-force lookups into O(log n) queries.

---

## 🌟 Why Segment Trees?

With 1 week of minute-by-minute stock data, we're working with up to **10,080 data points** (7 × 24 × 60). Non-effecient brute force scanning for min/max/mean would hit every single data point.

| Operation | Without Segment Tree | With Segment Tree |
|-----------|---------------------|-------------------|
| Build     | —                   | O(n)              |
| Max query | O(n) = ~10,080 ops  | O(log n) ≈ **14 ops** |
| Min query | O(n) = ~10,080 ops  | O(log n) ≈ **14 ops** |
| Sum/Mean  | O(n) = ~10,080 ops  | O(log n) ≈ **14 ops** |

> `log₂(10,080) ≈ 13.3` — a **700× speedup** on range queries.

---

## ✨ Features

- **Live data fetching** using `yfinance` (yahoo finance) — pulls 7-day, 1-minute interval closing prices for any valid ticker
- **CSV caching** — saves fetched data locally, allows for reload without connecting to the API again
- **Three segment trees** built in parallel: `max_tree`, `min_tree`, `sum_tree`
- **Six analytics operations** :
  - 🔺 Maximum price — `O(log n)`
  - 🔻 Minimum price — `O(log n)`
  - ➕ Sum of prices — `O(log n)`
  - ➗ Mean price — `O(log n)`
  - 📊 Price range (max − min) — `O(log n)`
  - 📦 Interquartile Range (IQR) — `O(n log n)`
- **Smart datetime parsing** — accepts multiple datetime input formats with binary-search index mapping to the actual stock data retrived from API

---

## 🗂️ Project Structure

```
StockAnalysis/
│
├── StockAnalysis.py          # Main entry point: data fetching, tree construction, query loop
├── Segment_tree_adt.py       # Segment tree ADT: build, query, and analytics functions
├── Segmenttree_testcases.py  # Unit tests for the segment tree implementation
│
├── AAPL__2026-04-30.csv      # Example cached data (Apple)
├── GOOG__2026-04-30.csv      # Example cached data (Google)
└── MSFT__2026-04-30.csv      # Example cached data (Microsoft)
```

---

## ⚙️ Setup & Installation

**Prerequisites:** Python 3.8+

```bash
# 1. Clone the repository
git clone https://github.com/AliH500/StockAnalysis.git
cd StockAnalysis

# 2. Install dependencies
pip install yfinance pandas
```

---

## 🚀 Usage

```bash
python StockAnalysis.py
```

**Step 1 — Enter a ticker:**
```
Enter stock ticker (e.g. AAPL, MSFT, TSLA): AAPL
Fetching 1 week data for AAPL...
2184 rows saved to 'AAPL__2026-04-30 11_09.csv'
```

**Step 2 — Choose a query from the menu:**
```
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
```

**Step 3 — Enter a datetime range:**
```
Start datetime: 2026-04-28 09:30
End datetime:   2026-04-28 16:00

Actual range:  2026-04-28 09:30:00  ->  2026-04-28 16:00:00
Data points in range: 390

>>> MAX price in range: $213.4200
```

---

## 📐 Segment Tree Implementation

Each tree node stores the **aggregate value** (max, min, or sum) for its subarray. The tree is stored as an array of size `2 × 2^⌈log₂(n)⌉ − 1`.

```
                [max: 213.42]           ← root covers entire range
               /             \
      [max: 211.10]      [max: 213.42]  ← covers left/right halves
       /        \           /        \
  [210.50]  [211.10]   [209.80]  [213.42]  ← leaf nodes
```

**Supported datetime input formats:**

| Format | Example |
|--------|---------|
| `YYYY-MM-DD HH:MM` | `2026-04-28 09:30` |
| `DD/MM/YYYY HH:MM` | `28/04/2026 09:30` |
| `DD-MM-YYYY HH:MM` | `28-04-2026 09:30` |
| `DD MMM YYYY HH:MM` | `28 Apr 2026 09:30` |

---

## 🧪 Running Tests

```bash
python Segmenttree_testcases.py
```

---

## 📚 References

- GeeksforGeeks — [Segment Tree](https://www.geeksforgeeks.org/segment-tree-data-structure/)
- YouTube — [Segment Tree Build & Query Walkthrough](https://www.youtube.com/watch?v=-dUiRtJ8ot0)
- Stack Overflow — Array sizing for segment trees (`4n` allocation)
- [`yfinance`](https://pypi.org/project/yfinance/) — Yahoo Finance market data library

---

## 👥 Authors

| Name | Role |
|------|------|
| **Ali Hani** | Solo-Developer |

---

<div align="center">
  <sub>Built with Python 🐍 · Powered by Segment Trees 🌲 · Data from Yahoo Finance 📊</sub>
</div>
