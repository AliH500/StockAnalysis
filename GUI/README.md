# Stock Analysis — GUI

CustomTkinter-based desktop GUI for the segment-tree stock analyser.
Reuses the original segment-tree ADT and binary-search index lookup from
the root-level CLI app; replaces the data-fetch + presentation layers.

## Ground rule

The original files at the repo root (`StockAnalysis.py`,
`Segment_tree_adt.py`, `Segmenttree_testcases.py`, the cached `*.csv`
files, and the root `README.md`) are **read-only**. All new GUI code,
docs, and assets live under this `GUI/` folder. The original segment-tree
module is imported, not edited.

## Setup

From the repo root:

```bash
cd projects/stock-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r GUI/requirements.txt
```

### Font (Nunito Medium)

The GUI is designed around Nunito Medium 500 but degrades gracefully if
the font isn't available — both `customtkinter` and `matplotlib` fall
back to a system default rounded sans.

For the intended look:

1. Download `Nunito-Medium.ttf` from
   [fonts.google.com/specimen/Nunito](https://fonts.google.com/specimen/Nunito)
   (or any mirror).
2. Drop it at `GUI/fonts/Nunito-Medium.ttf`.

When present, the file is:

- Auto-registered with `matplotlib.font_manager` at app start, so chart
  text uses Nunito unconditionally.
- Loaded into Tk via `tkextrafont` (optional dependency in
  `requirements.txt`) so CTk widgets use Nunito without a system-wide
  font install. If `tkextrafont` is missing, Tk widgets fall back; the
  chart still uses Nunito.

## Run

From the repo root (same level as `StockAnalysis.py`):

```bash
python GUI/main.py
```

## Modules

| File | Role |
|---|---|
| `main.py` | Entry point. |
| `main_window.py` | Top-level window, layout, fetch thread lifecycle, theme toggle. |
| `app_state.py` | Mutable container holding the fetched series and the three segment trees; the only file that touches V1 root via `sys.path`. |
| `data_loader.py` | yfinance wrapper. Returns the 7-day, 1-minute series with timestamps in the system local zone (fixes the CLI's naive-UTC bug). |
| `chart_widget.py` | Embedded matplotlib chart with a vertical gradient fill under the price line (pcolormesh + data-coordinate clip). |
| `analytics_panel.py` | Six-metric display. Two instances: full-week and selected-range. |
| `range_panel.py` | Start/end date pickers (`tkcalendar.DateEntry`) + HH:MM spinners. Resolves user input to segment-tree indices via the V1 binary search. |
| `theme.py` | Dark and light palettes + `apply_chart_style` for matplotlib repaint on theme toggle. |
| `fonts/Nunito-Medium.ttf` | Bundled font (user-supplied — see Font section). |

## Smoke test

1. `python GUI/main.py` opens a dark-themed window.
2. Chart area shows the placeholder "Enter a ticker to begin".
3. Type `AAPL` (or any valid ticker) into the ticker box, press Enter or
   click **Load**.
4. The button disables, "Fetching AAPL..." appears, UI stays responsive.
5. After 1–3 s the chart renders the full 7-day curve with a gradient
   fill; both analytics panels populate.
6. Pick a sub-range with the start/end date pickers and spinners — the
   chart shades the selected window and the "Selected range" panel
   updates immediately.
7. Toggle the **Light mode** switch — the entire app repaints; chart
   gradient and gridlines adopt the light palette without recreating
   widgets.

## Known constraints

- yfinance window fixed at 7 days, 1-minute interval (the CLI's choice;
  kept for parity).
- No CSV cache yet — every Load hits yfinance fresh. Add later if usage
  warrants it.
- No multi-ticker comparison, streaming, or accounts.
- US/EU exchanges only (yfinance limitation).

## Why a separate `GUI/` folder

- Keeps the original DSA-coursework submission intact and citable.
- Lets the GUI rewrite evolve freely without disturbing V1.
- Makes the diff for the LinkedIn showcase obvious: CLI at the root,
  GUI under `GUI/`.
