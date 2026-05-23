# Stock Analysis — GUI

This folder holds the GUI rewrite of the original CLI app. The GUI reuses
the original segment-tree ADT unchanged and replaces only the data-fetch
and presentation layers.

## Ground rule

The original files at the repo root (`StockAnalysis.py`,
`Segment_tree_adt.py`, `Segmenttree_testcases.py`, the cached `*.csv`
files, and the root `README.md`) are **read-only**. All new GUI code,
docs, and assets live under this `GUI/` folder. The original segment-tree
module is imported, not edited.

## Modules

- `data_loader.py` — yfinance wrapper that returns the 7-day,
  1-minute close-price series for a ticker with timestamps converted to
  the **system's local timezone**. Fixes the original timezone bug
  (the CLI version stripped tz info after converting to UTC, leaving
  naive-UTC datetimes that misread as local wall-clock time).

The GUI app entry point, the chart widget, and the analytics panels will
land here once the framework is locked in.

## Why a separate `GUI/` folder

- Keeps the original DSA-coursework submission intact and citable.
- Lets the GUI rewrite evolve freely (new file layout, naming,
  dependencies) without disturbing the original history.
- Makes the diff for the LinkedIn showcase obvious: CLI version at the
  root, GUI version under `GUI/`.
