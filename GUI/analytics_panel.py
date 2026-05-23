"""
Six-metric analytics panel. Two instances are mounted by `main_window`:
one for the full 7-day window, one for the user-selected sub-range.
Both call the same V1 segment-tree functions.
"""

from __future__ import annotations

import customtkinter as ctk

from app_state import AppState
from theme import FONT_FAMILY

# `v1_bridge` (loaded transitively via `app_state` above) inserts the V1
# root onto sys.path, so the unqualified import below resolves.
# `Segment_tree_adt.py` is a pure function library with no auto-execute,
# so importing from it directly is safe (unlike V1's `StockAnalysis.py`).
from Segment_tree_adt import (  # noqa: E402
    query_max,
    query_min,
    query_sum,
    get_mean,
    get_range,
    get_IQR,
)

METRIC_LABELS = ("Max", "Min", "Sum", "Mean", "Range", "IQR")
PLACEHOLDER = "—"


class AnalyticsPanel(ctk.CTkFrame):
    """`mode` is 'week' (full range) or 'range' (sub-range from RangePanel)."""

    def __init__(
        self,
        parent,
        state: AppState,
        title: str,
        mode: str,
        palette: dict,
    ):
        super().__init__(
            parent,
            fg_color=palette["panel_bg"],
            corner_radius=12,
            border_width=1,
            border_color=palette["panel_border"],
        )
        assert mode in ("week", "range")
        self._state = state
        self._mode = mode
        self._palette = palette

        self._title_label = ctk.CTkLabel(
            self,
            text=title,
            font=(FONT_FAMILY, 13, "bold"),
            text_color=palette["text_secondary"],
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 6))

        self._value_labels: dict[str, ctk.CTkLabel] = {}
        for i, name in enumerate(METRIC_LABELS):
            name_label = ctk.CTkLabel(
                self,
                text=name,
                font=(FONT_FAMILY, 12),
                text_color=palette["text_secondary"],
                anchor="w",
            )
            name_label.grid(row=i + 1, column=0, sticky="ew", padx=(14, 6), pady=2)

            value_label = ctk.CTkLabel(
                self,
                text=PLACEHOLDER,
                font=(FONT_FAMILY, 14),
                text_color=palette["text_primary"],
                anchor="e",
            )
            value_label.grid(row=i + 1, column=1, sticky="ew", padx=(6, 14), pady=2)
            self._value_labels[name] = value_label

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_theme(self, palette: dict) -> None:
        self._palette = palette
        self.configure(fg_color=palette["panel_bg"], border_color=palette["panel_border"])
        self._title_label.configure(text_color=palette["text_secondary"])
        for name, value_label in self._value_labels.items():
            value_label.configure(text_color=palette["text_primary"])
            # The name labels share the title's secondary tone; reach them
            # via grid_slaves to avoid keeping a second dict.
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child not in self._value_labels.values() and child is not self._title_label:
                child.configure(text_color=palette["text_secondary"])

    def refresh(self) -> None:
        if not self._state.has_data:
            for value_label in self._value_labels.values():
                value_label.configure(text=PLACEHOLDER)
            return

        n = len(self._state.closes)
        if self._mode == "week":
            l, r = self._state.week_indices()
        else:
            l, r = self._state.range_l, self._state.range_r
            if l > r:
                l, r = r, l

        max_val = query_max(0, 0, n - 1, l, r, self._state.max_tree)
        min_val = query_min(0, 0, n - 1, l, r, self._state.min_tree)
        sum_val = query_sum(0, 0, n - 1, l, r, self._state.sum_tree)
        mean_val = get_mean(0, 0, n - 1, l, r, self._state.sum_tree)
        range_val = get_range(
            0, 0, n - 1, l, r, self._state.max_tree, self._state.min_tree
        )
        iqr_val = get_IQR(self._state.closes, l, r)

        values = {
            "Max": max_val,
            "Min": min_val,
            "Sum": sum_val,
            "Mean": mean_val,
            "Range": range_val,
            "IQR": iqr_val,
        }
        for name, val in values.items():
            self._value_labels[name].configure(text=f"${val:,.4f}")
