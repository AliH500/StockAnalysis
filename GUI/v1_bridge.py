"""
Inlined copies of the two V1 utility functions we need: `build_trees`
and `datetime_to_index`.

Why this file exists: V1's `StockAnalysis.py` ends with a bare `main()`
call with no `if __name__ == "__main__":` guard, so importing anything
from it kicks off the CLI prompt and blocks the GUI from launching.
V1 is read-only, so the fix is to import only from `Segment_tree_adt.py`
(pure function library, import-safe) and re-implement the two tiny
wrappers here. Behaviour is bit-for-bit identical to the V1 originals.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Segment_tree_adt import (  # noqa: E402
    build_max,
    build_min,
    build_sum,
    create_tree,
)


def build_trees(close_prices: list[float]):
    n = len(close_prices)
    max_tree = create_tree(close_prices)
    min_tree = create_tree(close_prices)
    sum_tree = create_tree(close_prices)
    build_max(0, 0, n - 1, max_tree, close_prices)
    build_min(0, 0, n - 1, min_tree, close_prices)
    build_sum(0, 0, n - 1, sum_tree, close_prices)
    return max_tree, min_tree, sum_tree


def datetime_to_index(target: datetime, timestamps: list[datetime]) -> int:
    lo, hi = 0, len(timestamps) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if timestamps[mid] == target:
            return mid
        elif timestamps[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if lo == 0:
        return 0
    if lo >= len(timestamps):
        return len(timestamps) - 1
    before = abs(timestamps[lo - 1] - target)
    after = abs(timestamps[lo] - target)
    return lo - 1 if before <= after else lo
