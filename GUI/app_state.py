"""
Single mutable container for everything the UI reads or writes.

All widgets receive one `AppState` and either read from it or mutate
`range_l` / `range_r` and trigger a redraw via callbacks. The state is
single-writer on the Tk main thread; the background fetch thread only
posts results to a `queue.Queue` and never touches this object.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# V1's `StockAnalysis.py` and `Segment_tree_adt.py` live one level up at
# the nested-repo root. Adding the parent dir to sys.path is the cleanest
# import path that does not require restructuring the read-only V1 files.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from StockAnalysis import build_trees  # noqa: E402

from data_loader import StockSeries  # noqa: E402


@dataclass
class AppState:
    series: StockSeries | None = None
    closes: list[float] = field(default_factory=list)
    timestamps: list[datetime] = field(default_factory=list)
    # tz-naive parallel index used only for V1's `datetime_to_index`
    # binary search, which compares timestamps with raw `<`/`>` operators
    # and crashes on tz-aware vs tz-naive mixes.
    timestamps_naive: list[datetime] = field(default_factory=list)
    max_tree: list | None = None
    min_tree: list | None = None
    sum_tree: list | None = None
    range_l: int = 0
    range_r: int = 0

    @property
    def has_data(self) -> bool:
        return self.series is not None and len(self.closes) > 0

    def load(self, series: StockSeries) -> None:
        self.series = series
        self.closes = list(series.closes)
        self.timestamps = list(series.timestamps)
        self.timestamps_naive = [ts.replace(tzinfo=None) for ts in series.timestamps]
        # `build_trees` prints progress lines to stdout; harmless under a GUI.
        self.max_tree, self.min_tree, self.sum_tree = build_trees(self.closes)
        self.range_l = 0
        self.range_r = len(self.closes) - 1

    def week_indices(self) -> tuple[int, int]:
        if not self.has_data:
            return (0, 0)
        return (0, len(self.closes) - 1)
