"""
Range-query panel: two (date-picker + HH/MM spinner) blocks for start
and end, wired to V1's `datetime_to_index` binary search.

Critical correctness note: V1 stores tz-naive datetimes (the CLI converts
to UTC and strips tzinfo). The GUI's `data_loader` returns tz-aware
local-zone datetimes. To call V1's `datetime_to_index` without crashing
on the aware-vs-naive comparison, this panel resolves the user's input
against `state.timestamps_naive` (parallel array stripped at load time
in `AppState.load`).
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, time
from tkinter import ttk
from typing import Callable

import customtkinter as ctk
from tkcalendar import DateEntry

from app_state import AppState
from theme import FONT_FAMILY

# `app_state` (imported above) inserts the V1 root onto sys.path, so the
# unqualified import below resolves to V1's `StockAnalysis.py`.
from StockAnalysis import datetime_to_index  # noqa: E402


class _DateTimePicker(ctk.CTkFrame):
    """One row: label + DateEntry + HH spinbox + MM spinbox."""

    def __init__(self, parent, label: str, palette: dict, on_change: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self._on_change = on_change
        self._palette = palette

        ctk.CTkLabel(
            self,
            text=label,
            font=(FONT_FAMILY, 12),
            text_color=palette["text_secondary"],
            width=46,
            anchor="w",
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        # tkcalendar.DateEntry — pure ttk widget; theme via direct kwargs.
        self.date_entry = DateEntry(
            self,
            width=10,
            background=palette["accent"],
            foreground="white",
            bordercolor=palette["panel_border"],
            headersbackground=palette["panel_bg"],
            headersforeground=palette["text_primary"],
            normalbackground=palette["panel_bg"],
            normalforeground=palette["text_primary"],
            weekendbackground=palette["panel_bg"],
            weekendforeground=palette["text_secondary"],
            othermonthbackground=palette["bg"],
            othermonthforeground=palette["text_secondary"],
            selectbackground=palette["accent"],
            selectforeground="white",
            date_pattern="yyyy-mm-dd",
            state="disabled",
        )
        self.date_entry.grid(row=0, column=1, padx=(0, 8))
        self.date_entry.bind("<<DateEntrySelected>>", lambda _e: self._on_change())

        self.hh = tk.StringVar(value="00")
        self.mm = tk.StringVar(value="00")

        self.hh_spin = tk.Spinbox(
            self,
            from_=0,
            to=23,
            width=3,
            textvariable=self.hh,
            format="%02.0f",
            wrap=True,
            font=(FONT_FAMILY, 11),
            state="disabled",
        )
        self.hh_spin.grid(row=0, column=2)

        ctk.CTkLabel(
            self, text=":", font=(FONT_FAMILY, 12), text_color=palette["text_secondary"]
        ).grid(row=0, column=3, padx=2)

        self.mm_spin = tk.Spinbox(
            self,
            from_=0,
            to=59,
            width=3,
            textvariable=self.mm,
            format="%02.0f",
            wrap=True,
            font=(FONT_FAMILY, 11),
            state="disabled",
        )
        self.mm_spin.grid(row=0, column=4)

        for spin in (self.hh_spin, self.mm_spin):
            spin.bind("<FocusOut>", lambda _e: self._on_change())
            spin.bind("<Increment>", lambda _e: self.after(1, self._on_change))
            spin.bind("<Decrement>", lambda _e: self.after(1, self._on_change))

        self._apply_spinbox_style(palette)

    def _apply_spinbox_style(self, palette: dict) -> None:
        for spin in (self.hh_spin, self.mm_spin):
            spin.configure(
                bg=palette["spinbox_bg"],
                fg=palette["spinbox_fg"],
                buttonbackground=palette["spinbox_button"],
                insertbackground=palette["spinbox_fg"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=palette["panel_border"],
                highlightcolor=palette["accent"],
            )

    def apply_theme(self, palette: dict) -> None:
        self._palette = palette
        self._apply_spinbox_style(palette)
        # DateEntry can't be reconfigured wholesale post-construction, but
        # the colour kwargs that matter for the popup are accepted via
        # configure() one at a time on tkcalendar >= 1.6.
        try:
            self.date_entry.configure(
                background=palette["accent"],
                headersbackground=palette["panel_bg"],
                headersforeground=palette["text_primary"],
                normalbackground=palette["panel_bg"],
                normalforeground=palette["text_primary"],
                weekendbackground=palette["panel_bg"],
                weekendforeground=palette["text_secondary"],
                othermonthbackground=palette["bg"],
                othermonthforeground=palette["text_secondary"],
                selectbackground=palette["accent"],
            )
        except tk.TclError:
            pass

    def enable(self) -> None:
        self.date_entry.configure(state="normal")
        self.hh_spin.configure(state="normal")
        self.mm_spin.configure(state="normal")

    def get_datetime(self) -> datetime:
        d = self.date_entry.get_date()
        try:
            hh = max(0, min(23, int(self.hh.get())))
            mm = max(0, min(59, int(self.mm.get())))
        except ValueError:
            hh, mm = 0, 0
        return datetime.combine(d, time(hh, mm))


class RangePanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        state: AppState,
        palette: dict,
        on_range_change: Callable[[], None],
    ):
        super().__init__(
            parent,
            fg_color=palette["panel_bg"],
            corner_radius=12,
            border_width=1,
            border_color=palette["panel_border"],
        )
        self._state = state
        self._palette = palette
        self._on_range_change = on_range_change
        self._warning_after_id: str | None = None

        self._title = ctk.CTkLabel(
            self,
            text="Range query",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=palette["text_secondary"],
            anchor="w",
        )
        self._title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))

        self.start_picker = _DateTimePicker(self, "Start", palette, self._handle_change)
        self.start_picker.grid(row=1, column=0, sticky="ew", padx=14, pady=4)

        self.end_picker = _DateTimePicker(self, "End", palette, self._handle_change)
        self.end_picker.grid(row=2, column=0, sticky="ew", padx=14, pady=4)

        self._warning = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, 11),
            text_color=palette["warning_text"],
            anchor="w",
        )
        self._warning.grid(row=3, column=0, sticky="ew", padx=14, pady=(2, 12))

        self.grid_columnconfigure(0, weight=1)

    def apply_theme(self, palette: dict) -> None:
        self._palette = palette
        self.configure(fg_color=palette["panel_bg"], border_color=palette["panel_border"])
        self._title.configure(text_color=palette["text_secondary"])
        self._warning.configure(text_color=palette["warning_text"])
        self.start_picker.apply_theme(palette)
        self.end_picker.apply_theme(palette)

    def configure_bounds(self) -> None:
        """Called after a fresh data load. Constrains date pickers and seeds defaults."""
        if not self._state.has_data:
            return
        ts = self._state.timestamps
        first = ts[0]
        last = ts[-1]
        for picker in (self.start_picker, self.end_picker):
            picker.enable()
            picker.date_entry.configure(mindate=first.date(), maxdate=last.date())

        self.start_picker.date_entry.set_date(first.date())
        self.start_picker.hh.set(f"{first.hour:02d}")
        self.start_picker.mm.set(f"{first.minute:02d}")

        self.end_picker.date_entry.set_date(last.date())
        self.end_picker.hh.set(f"{last.hour:02d}")
        self.end_picker.mm.set(f"{last.minute:02d}")

        self._state.range_l = 0
        self._state.range_r = len(self._state.timestamps) - 1

    def _handle_change(self) -> None:
        if not self._state.has_data:
            return
        try:
            start_dt = self.start_picker.get_datetime()
            end_dt = self.end_picker.get_datetime()
        except Exception:
            return

        swapped = False
        if end_dt < start_dt:
            start_dt, end_dt = end_dt, start_dt
            swapped = True

        l = datetime_to_index(start_dt, self._state.timestamps_naive)
        r = datetime_to_index(end_dt, self._state.timestamps_naive)
        if l > r:
            l, r = r, l

        self._state.range_l = l
        self._state.range_r = r

        if swapped:
            self._show_warning("End was before start — swapped.")
        else:
            self._clear_warning()

        self._on_range_change()

    def _show_warning(self, text: str) -> None:
        self._warning.configure(text=text)
        if self._warning_after_id is not None:
            try:
                self.after_cancel(self._warning_after_id)
            except Exception:
                pass
        self._warning_after_id = self.after(3000, self._clear_warning)

    def _clear_warning(self) -> None:
        self._warning.configure(text="")
        self._warning_after_id = None
