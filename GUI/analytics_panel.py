"""
Six-metric analytics panel. Two instances are mounted by `main_window`:
one for the full 7-day window, one for the user-selected sub-range.
Both call the same V1 segment-tree functions.
"""

from __future__ import annotations

import customtkinter as ctk

from app_state import AppState
from theme import FONT_FAMILY, FONT_SIZES

# `app_state` (imported above) inserts the V1 root onto sys.path, so the
# unqualified import below resolves to the V1 segment-tree ADT.
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
            corner_radius=14,
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
            font=(FONT_FAMILY, FONT_SIZES["section"], "bold"),
            text_color=palette["text_primary"],
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(16, 10))

        self._name_labels: list[ctk.CTkLabel] = []
        self._value_labels: dict[str, ctk.CTkLabel] = {}
        for i, name in enumerate(METRIC_LABELS):
            name_label = ctk.CTkLabel(
                self,
                text=name,
                font=(FONT_FAMILY, FONT_SIZES["label"]),
                text_color=palette["text_secondary"],
                anchor="w",
            )
            name_label.grid(row=i + 1, column=0, sticky="ew", padx=(18, 8), pady=4)
            self._name_labels.append(name_label)

            value_label = ctk.CTkLabel(
                self,
                text=PLACEHOLDER,
                font=(FONT_FAMILY, FONT_SIZES["metric"], "bold"),
                text_color=palette["text_primary"],
                anchor="e",
            )
            value_label.grid(row=i + 1, column=1, sticky="ew", padx=(8, 18), pady=4)
            self._value_labels[name] = value_label

        # Tail spacer so the bottom row isn't flush against the border.
        ctk.CTkLabel(self, text="").grid(row=len(METRIC_LABELS) + 1, column=0, pady=4)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_theme(self, palette: dict) -> None:
        self._palette = palette
        self.configure(fg_color=palette["panel_bg"], border_color=palette["panel_border"])
        self._title_label.configure(text_color=palette["text_primary"])
        for value_label in self._value_labels.values():
            value_label.configure(text_color=palette["text_primary"])
        for name_label in self._name_labels:
            name_label.configure(text_color=palette["text_secondary"])

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
