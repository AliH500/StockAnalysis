# Stock Analysis — V2 (GUI rewrite)

V2 is the GUI replacement for the original CLI app. It reuses the V1
segment-tree ADT unchanged and replaces the data-fetch and presentation
layers.

## Ground rule

The original V1 files at the repo root (`StockAnalysis.py`,
`Segment_tree_adt.py`, `Segmenttree_testcases.py`, the cached `*.csv`
files, and the root `README.md`) are **read-only**. All new V2 code,
docs, and assets live under this `v2/` folder. V1 is imported, not
edited.

## Modules

- `data_loader.py` — yfinance wrapper that returns the 7-day,
  1-minute close-price series for a ticker with timestamps converted to
  the **system's local timezone**. Fixes the V1 timezone bug
  (V1 stripped tz info after converting to UTC, leaving naive-UTC
  datetimes that misread as local wall-clock time).

More modules land here as the GUI is built.

## Why a separate `v2/` folder

- Keeps the original DSA-coursework submission intact and citable.
- Lets V2 evolve freely (new file layout, naming, dependencies) without
  disturbing the V1 history.
- Makes the diff for the LinkedIn showcase obvious: V1 = CLI, V2 = GUI.
