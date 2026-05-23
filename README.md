# 📈 StockAnalysis — Range Analytics using Segment trees

> **DSA Project** by **Ali Hani** · *Prof. Nadia Nasir, L3*

A Python application that fetches real-time stock data and performs lightning-fast range-based analytics using **Segment Trees** — turning O(n) brute-force lookups into O(log n) queries. Ships in two flavours: the original **command-line tool** and a polished **desktop GUI**.

---

## 🚀 Try the GUI demo

The GUI is a single-window desktop app with a gradient price chart, six segment-tree analytics across both the full week and a user-defined sub-range, and a custom date picker.

**Download the pre-built executable** from the [latest GitHub release](https://github.com/AliH500/StockAnalysis/releases/latest) — no Python install required. (Windows only)


> If your machine doesn't have Nunito installed system-wide, the GUI's Tk widgets fall back to a default sans. The hero chart always uses the bundled Nunito.

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
- **GUI extras** — green/red price line that flips at the 7-day-ago baseline, gradient fill, custom date picker, dark/light theme toggle, all timestamps shown in the user's local timezone

---

## 🗂️ Project Structure

```
StockAnalysis/
│
├── StockAnalysis.py          # CLI entry point: data fetching, tree construction, query loop
├── Segment_tree_adt.py       # Segment tree ADT: build, query, and analytics functions
├── Segmenttree_testcases.py  # Unit tests for the segment tree implementation
│
├── AAPL__2026-04-30.csv      # Example cached data (Apple)
├── GOOG__2026-04-30.csv      # Example cached data (Google)
├── MSFT__2026-04-30.csv      # Example cached data (Microsoft)
│
└── GUI/                      # Desktop GUI rewrite
    ├── main.py               # Entry point
    ├── main_window.py        # Window, layout, fetch thread, theme toggle
    ├── chart_widget.py       # Matplotlib chart with gradient fill + green/red line
    ├── analytics_panel.py    # Six-metric panel (full-week and sub-range)
    ├── range_panel.py        # Date pickers + HH/MM spinners + custom calendar
    ├── data_loader.py        # yfinance wrapper, timestamps in system local zone
    ├── app_state.py          # Mutable state shared across widgets
    ├── theme.py              # Dark + light palettes, type scale
    ├── build.sh              # PyInstaller build script
    ├── requirements.txt      # Python dependencies
    └── fonts/Nunito-*.ttf    # Bundled font family
```

---

## ⚙️ CLI Setup & Installation

**Prerequisites:** Python 3.8+

```bash
# 1. Clone the repository
git clone https://github.com/AliH500/StockAnalysis.git
cd StockAnalysis

# 2. Install dependencies
pip install yfinance pandas
```

---

## 🚀 CLI Usage

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

## 🛠️ Run the GUI from source

For contributors and anyone who'd rather skip the executable.

### Required system packages

The GUI uses Tk + PIL's Tk bindings, both of which Linux distros split out from the base Python install:

| OS | Install |
|---|---|
| Fedora / RHEL | `sudo dnf install python3-tkinter python3-pillow-tk` |
| Ubuntu / Debian | `sudo apt install python3-tk python3-pil.imagetk` |
| Arch | `sudo pacman -S tk python-pillow` |
| macOS | Tk ships with the python.org installer; Pillow via pip |
| Windows | Tk ships with the python.org installer; Pillow via pip |

### Python dependencies

```bash
cd StockAnalysis
python3 -m pip install --user -r GUI/requirements.txt
```

This pulls in:

- `customtkinter` — modern Tk widget library
- `matplotlib` — embedded chart with gradient fill
- `tkcalendar` — historical dep, retained but the popup is now custom
- `yfinance` + `pandas` — data fetch
- `Pillow` — image support for CustomTkinter
- `tkextrafont` — *optional*; lets the bundled Nunito font load into Tk widgets without a system-wide font install. Build prerequisites (Tcl/Tk dev headers + scikit-build) often need a system install; safe to skip — the GUI falls back to system fonts for Tk widgets.

### Launch

From the repo root:

```bash
python3 GUI/main.py
```

### Build your own executable

**Linux / macOS:**

```bash
bash GUI/build.sh
```

**Windows** (PowerShell — note the `;` data separator instead of `:`):

```powershell
python -m PyInstaller `
    --noconfirm --clean --onefile --windowed `
    --name StockAnalysis `
    --paths GUI `
    --add-data "GUI/fonts;fonts" `
    --add-data "StockAnalysis.py;v1" `
    --add-data "Segment_tree_adt.py;v1" `
    --collect-all customtkinter `
    --collect-all tkcalendar `
    --hidden-import PIL._tkinter_finder `
    GUI/main.py
```

Output: `dist/StockAnalysis` (Linux/macOS) or `dist/StockAnalysis.exe` (Windows). The build bundles the segment-tree modules, the **entire** Nunito font family (Regular / Medium / Bold / Italic / etc., so weights render with real glyphs instead of faux-bolded Medium), and all CustomTkinter assets into a single file.

**On Windows the GUI loads Nunito via `AddFontResourceExW` (Win32 GDI) — no `tkextrafont` dependency, no system-wide font install, no admin rights.** The Tk widgets will render in Nunito on every Windows machine that runs the executable.

> **Cross-platform note:** PyInstaller does not cross-compile. To produce a Windows `.exe`, run the PowerShell command above on a Windows machine; for macOS, on macOS.

---

<div align="center">
  <sub>Built with Python 🐍 · Powered by Segment Trees 🌲 · Data from Yahoo Finance 📊</sub>
</div>
