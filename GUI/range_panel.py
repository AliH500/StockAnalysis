"""
Range-query panel: a 2-row grid of (date-button + HH spinbox + MM spinbox)
for Start and End, with column headers (Date / Hour / Minute).

The date button opens a custom `tk.Toplevel` calendar popup. Each date
cell is a raw `tk.Canvas` with an oval + text item — that bypasses every
CustomTkinter rendering quirk inside a popup and renders the day numbers
reliably on every WM tested.

Critical correctness note: V1's `datetime_to_index` lives in
`StockAnalysis.py` and compares datetimes with raw `<`/`>` — it only
works on tz-naive datetimes. The GUI's `data_loader` returns tz-aware
local-zone timestamps; `AppState.load` keeps a parallel
`timestamps_naive` list for this lookup.
"""

from __future__ import annotations

import calendar as cal_module
import tkinter as tk
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable

import customtkinter as ctk

from app_state import AppState
from theme import FONT_FAMILY, FONT_SIZES

# `app_state` (imported above) inserts the V1 root onto sys.path, so the
# unqualified import below resolves to V1's `StockAnalysis.py`.
from StockAnalysis import datetime_to_index  # noqa: E402


# --------------------------------------------------------------------------- #
#  Calendar popup                                                             #
# --------------------------------------------------------------------------- #


@dataclass
class _CalCell:
    canvas: tk.Canvas
    oval_id: int
    text_id: int
    date: date | None = None
    in_range: bool = False
    # "active" (in-month, clickable) / "muted" (other-month) /
    # "selected" / "disabled" (out-of-data-range).
    state: str = "muted"


class _CalendarPopup(tk.Toplevel):
    """Borderless month picker built entirely from raw Tk widgets."""

    DAY_LABELS = ("S", "M", "T", "W", "T", "F", "S")  # Sunday-first
    CELL = 44   # cell width/height in px
    PAD = 3     # outer padding around the oval inside the cell

    def __init__(
        self,
        master,
        palette: dict,
        selected: date,
        min_date: date,
        max_date: date,
        on_select: Callable[[date], None],
        anchor_widget,
    ):
        super().__init__(master)
        self._palette = palette
        self._selected = selected
        self._min = min_date
        self._max = max_date
        self._on_select = on_select
        self._month_view = selected.replace(day=1)

        self.overrideredirect(True)
        self.configure(bg=palette["panel_border"])  # 1 px border via outer bg
        self.attributes("-topmost", True)

        self._inner = tk.Frame(self, bg=palette["panel_bg"])
        self._inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._build()
        self._populate()
        self._position_below(anchor_widget)

        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(50, self._grab)

    def _grab(self) -> None:
        try:
            self.wait_visibility()
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def _position_below(self, anchor) -> None:
        self.update_idletasks()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 6
        w = self.CELL * 7 + 36
        h = self.CELL * 6 + 112
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self) -> None:
        p = self._palette

        # Header: prev | Month YYYY | next
        header = tk.Frame(self._inner, bg=p["panel_bg"])
        header.pack(fill="x", padx=16, pady=(14, 8))

        self._prev_btn = self._nav_button(header, "‹", self._prev_month)
        self._prev_btn.pack(side="left")

        self._month_label = tk.Label(
            header, text="",
            font=(FONT_FAMILY, FONT_SIZES["calendar_header"], "bold"),
            bg=p["panel_bg"], fg=p["text_primary"],
        )
        self._month_label.pack(side="left", expand=True)

        self._next_btn = self._nav_button(header, "›", self._next_month)
        self._next_btn.pack(side="right")

        # Day-of-week labels
        dow = tk.Frame(self._inner, bg=p["panel_bg"])
        dow.pack(padx=16, pady=(0, 4))
        for i, label in enumerate(self.DAY_LABELS):
            tk.Label(
                dow, text=label, width=3,
                font=(FONT_FAMILY, 11, "bold"),
                bg=p["panel_bg"], fg=p["text_muted"],
            ).grid(row=0, column=i, padx=3, pady=2)

        # Date grid: one tk.Canvas per cell, oval + centred text item.
        grid = tk.Frame(self._inner, bg=p["panel_bg"])
        grid.pack(padx=16, pady=(0, 14))

        self._cells: list[list[_CalCell]] = []
        for r in range(6):
            row: list[_CalCell] = []
            for c in range(7):
                canvas = tk.Canvas(
                    grid, width=self.CELL, height=self.CELL,
                    bg=p["panel_bg"], highlightthickness=0, bd=0,
                )
                canvas.grid(row=r, column=c, padx=1, pady=1)
                oval_id = canvas.create_oval(
                    self.PAD, self.PAD,
                    self.CELL - self.PAD, self.CELL - self.PAD,
                    fill="", outline="",
                )
                text_id = canvas.create_text(
                    self.CELL // 2, self.CELL // 2,
                    text="", fill=p["text_primary"],
                    font=(FONT_FAMILY, 14, "bold"),
                )
                cell = _CalCell(canvas=canvas, oval_id=oval_id, text_id=text_id)
                canvas.bind("<Button-1>", lambda _e, rr=r, cc=c: self._on_cell_click(rr, cc))
                canvas.bind("<Enter>", lambda _e, rr=r, cc=c: self._on_hover_enter(rr, cc))
                canvas.bind("<Leave>", lambda _e, rr=r, cc=c: self._on_hover_leave(rr, cc))
                row.append(cell)
            self._cells.append(row)

    def _nav_button(self, parent, text: str, command) -> tk.Button:
        p = self._palette
        return tk.Button(
            parent, text=text, width=2,
            font=(FONT_FAMILY, 18, "bold"),
            bg=p["panel_bg"], fg=p["text_primary"],
            activebackground=p["hover_bg"], activeforeground=p["text_primary"],
            disabledforeground=p["text_muted"],
            relief="flat", borderwidth=0, highlightthickness=0,
            cursor="hand2", command=command,
        )

    def _populate(self) -> None:
        year = self._month_view.year
        month = self._month_view.month
        self._month_label.configure(text=f"{cal_module.month_name[month]} {year}")

        first = date(year, month, 1)
        # Python's weekday: Mon=0, Sun=6. We want Sun=0 in column 0.
        offset = (first.weekday() + 1) % 7
        days_in_month = cal_module.monthrange(year, month)[1]

        prev_year = year if month > 1 else year - 1
        prev_month = month - 1 if month > 1 else 12
        prev_days = cal_module.monthrange(prev_year, prev_month)[1]
        next_year = year if month < 12 else year + 1
        next_month = month + 1 if month < 12 else 1

        # Leading slots from previous month
        for i in range(offset):
            day_num = prev_days - offset + 1 + i
            d = date(prev_year, prev_month, day_num)
            self._style_cell(self._cells[0][i], day_num, d, in_current_month=False)

        # Current month
        for day_num in range(1, days_in_month + 1):
            idx = offset + day_num - 1
            r, c = idx // 7, idx % 7
            d = date(year, month, day_num)
            self._style_cell(self._cells[r][c], day_num, d, in_current_month=True)

        # Trailing slots from next month
        filled = offset + days_in_month
        for i in range(42 - filled):
            day_num = i + 1
            idx = filled + i
            r, c = idx // 7, idx % 7
            d = date(next_year, next_month, day_num)
            self._style_cell(self._cells[r][c], day_num, d, in_current_month=False)

        prev_first = (first - timedelta(days=1)).replace(day=1)
        self._prev_btn.configure(
            state="normal" if prev_first >= self._min.replace(day=1) else "disabled"
        )
        next_first = date(next_year, next_month, 1)
        self._next_btn.configure(
            state="normal" if next_first <= self._max else "disabled"
        )

    def _style_cell(self, cell: _CalCell, day_num: int, d: date, *, in_current_month: bool) -> None:
        p = self._palette
        in_range = self._min <= d <= self._max
        is_selected = d == self._selected
        cell.date = d
        cell.in_range = in_range
        cell.canvas.itemconfig(cell.text_id, text=str(day_num))

        if is_selected and in_range:
            cell.state = "selected"
            cell.canvas.itemconfig(cell.oval_id, fill=p["accent"], outline="")
            cell.canvas.itemconfig(cell.text_id, fill="#FFFFFF")
        elif not in_range:
            cell.state = "disabled"
            cell.canvas.itemconfig(cell.oval_id, fill="", outline="")
            cell.canvas.itemconfig(cell.text_id, fill=p["text_muted"])
        elif not in_current_month:
            cell.state = "muted"
            cell.canvas.itemconfig(cell.oval_id, fill="", outline="")
            cell.canvas.itemconfig(cell.text_id, fill=p["text_muted"])
        else:
            cell.state = "active"
            cell.canvas.itemconfig(cell.oval_id, fill="", outline="")
            cell.canvas.itemconfig(cell.text_id, fill=p["text_primary"])

    def _on_hover_enter(self, r: int, c: int) -> None:
        cell = self._cells[r][c]
        if cell.state in ("active", "muted"):
            cell.canvas.itemconfig(cell.oval_id, fill=self._palette["hover_bg"])

    def _on_hover_leave(self, r: int, c: int) -> None:
        cell = self._cells[r][c]
        if cell.state in ("active", "muted"):
            cell.canvas.itemconfig(cell.oval_id, fill="")

    def _prev_month(self) -> None:
        if self._month_view.month == 1:
            self._month_view = self._month_view.replace(year=self._month_view.year - 1, month=12)
        else:
            self._month_view = self._month_view.replace(month=self._month_view.month - 1)
        self._populate()

    def _next_month(self) -> None:
        if self._month_view.month == 12:
            self._month_view = self._month_view.replace(year=self._month_view.year + 1, month=1)
        else:
            self._month_view = self._month_view.replace(month=self._month_view.month + 1)
        self._populate()

    def _on_cell_click(self, r: int, c: int) -> None:
        cell = self._cells[r][c]
        if cell.date is None or not cell.in_range:
            return
        self._on_select(cell.date)
        self.destroy()


# --------------------------------------------------------------------------- #
#  Range panel                                                                #
# --------------------------------------------------------------------------- #


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
            corner_radius=14,
            border_width=1,
            border_color=palette["panel_border"],
        )
        self._state = state
        self._palette = palette
        self._on_range_change = on_range_change
        self._warning_after_id: str | None = None
        self._suppress_change = False

        # Independent state per row.
        self._start_date: date | None = None
        self._end_date: date | None = None

        self._build()

    # ---- layout --------------------------------------------------------- #

    def _build(self) -> None:
        p = self._palette

        # Section title
        self._title = ctk.CTkLabel(
            self, text="Range query",
            font=(FONT_FAMILY, FONT_SIZES["section"], "bold"),
            text_color=p["text_primary"],
            anchor="w",
        )
        self._title.grid(row=0, column=0, columnspan=5, sticky="ew", padx=18, pady=(16, 10))

        # Column headers (row 1): blank | Date | Hour | : | Minute
        self._header_labels: list[ctk.CTkLabel] = []
        for col, text, sticky in (
            (1, "Date", "ew"),
            (2, "Hour", "ew"),
            (4, "Minute", "ew"),
        ):
            lbl = ctk.CTkLabel(
                self, text=text,
                font=(FONT_FAMILY, FONT_SIZES["small"], "bold"),
                text_color=p["text_secondary"],
            )
            lbl.grid(row=1, column=col, padx=4, pady=(0, 6))
            self._header_labels.append(lbl)

        # Start row (row 2)
        self._start_row_label, self._start_date_btn, self._start_hh, self._start_mm, \
            self._start_hh_spin, self._start_mm_spin, self._start_colon = \
            self._build_row(row=2, label_text="Start", on_calendar=self._open_start_calendar)

        # End row (row 3)
        self._end_row_label, self._end_date_btn, self._end_hh, self._end_mm, \
            self._end_hh_spin, self._end_mm_spin, self._end_colon = \
            self._build_row(row=3, label_text="End", on_calendar=self._open_end_calendar)

        # Warning (row 4)
        self._warning = ctk.CTkLabel(
            self, text="",
            font=(FONT_FAMILY, FONT_SIZES["small"]),
            text_color=p["warning_text"],
            anchor="w",
        )
        self._warning.grid(row=4, column=0, columnspan=5, sticky="ew", padx=18, pady=(8, 16))

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=0)

    def _build_row(self, *, row: int, label_text: str, on_calendar: Callable[[], None]):
        p = self._palette

        row_label = ctk.CTkLabel(
            self, text=label_text,
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            text_color=p["text_primary"],
            anchor="w",
        )
        row_label.grid(row=row, column=0, padx=(18, 12), pady=6, sticky="w")

        date_btn = ctk.CTkButton(
            self, text="—",
            width=160, height=36,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            fg_color=p["spinbox_bg"],
            hover_color=p["hover_bg"],
            text_color=p["text_primary"],
            border_width=1,
            border_color=p["panel_border"],
            corner_radius=8,
            anchor="w",
            command=on_calendar,
            state="disabled",
        )
        date_btn.grid(row=row, column=1, padx=4, pady=6, sticky="ew")

        hh = tk.StringVar(value="00")
        mm = tk.StringVar(value="00")
        hh.trace_add("write", lambda *_a: self._on_change())
        mm.trace_add("write", lambda *_a: self._on_change())

        hh_spin = tk.Spinbox(
            self, from_=0, to=23, width=4,
            textvariable=hh, format="%02.0f", wrap=True,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            state="disabled",
        )
        hh_spin.grid(row=row, column=2, padx=(4, 0), pady=6)

        colon = ctk.CTkLabel(
            self, text=":",
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            text_color=p["text_secondary"],
        )
        colon.grid(row=row, column=3, padx=2, pady=6)

        mm_spin = tk.Spinbox(
            self, from_=0, to=59, width=4,
            textvariable=mm, format="%02.0f", wrap=True,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            state="disabled",
        )
        mm_spin.grid(row=row, column=4, padx=(0, 18), pady=6)

        self._style_spinbox(hh_spin)
        self._style_spinbox(mm_spin)

        return row_label, date_btn, hh, mm, hh_spin, mm_spin, colon

    def _style_spinbox(self, spin: tk.Spinbox) -> None:
        p = self._palette
        spin.configure(
            bg=p["spinbox_bg"],
            fg=p["spinbox_fg"],
            buttonbackground=p["spinbox_button"],
            insertbackground=p["spinbox_fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=p["panel_border"],
            highlightcolor=p["accent"],
        )

    # ---- public API ----------------------------------------------------- #

    def apply_theme(self, palette: dict) -> None:
        self._palette = palette
        p = palette
        self.configure(fg_color=p["panel_bg"], border_color=p["panel_border"])
        self._title.configure(text_color=p["text_primary"])
        for lbl in self._header_labels:
            lbl.configure(text_color=p["text_secondary"])
        self._warning.configure(text_color=p["warning_text"])

        for row_lbl in (self._start_row_label, self._end_row_label):
            row_lbl.configure(text_color=p["text_primary"])
        for btn in (self._start_date_btn, self._end_date_btn):
            btn.configure(
                fg_color=p["spinbox_bg"],
                hover_color=p["hover_bg"],
                text_color=p["text_primary"],
                border_color=p["panel_border"],
            )
        for colon in (self._start_colon, self._end_colon):
            colon.configure(text_color=p["text_secondary"])
        for spin in (self._start_hh_spin, self._start_mm_spin,
                     self._end_hh_spin, self._end_mm_spin):
            self._style_spinbox(spin)

    def configure_bounds(self) -> None:
        """Called after a fresh data load."""
        if not self._state.has_data:
            return
        ts = self._state.timestamps
        first, last = ts[0], ts[-1]

        self._suppress_change = True
        try:
            self._start_date = first.date()
            self._end_date = last.date()
            self._start_date_btn.configure(text=self._start_date.isoformat(), state="normal")
            self._end_date_btn.configure(text=self._end_date.isoformat(), state="normal")
            self._start_hh.set(f"{first.hour:02d}")
            self._start_mm.set(f"{first.minute:02d}")
            self._end_hh.set(f"{last.hour:02d}")
            self._end_mm.set(f"{last.minute:02d}")
            for spin in (self._start_hh_spin, self._start_mm_spin,
                         self._end_hh_spin, self._end_mm_spin):
                spin.configure(state="normal")
        finally:
            self._suppress_change = False

        self._state.range_l = 0
        self._state.range_r = len(ts) - 1

    # ---- calendar handlers --------------------------------------------- #

    def _open_start_calendar(self) -> None:
        self._open_calendar(self._start_date_btn, self._start_date, self._set_start_date)

    def _open_end_calendar(self) -> None:
        self._open_calendar(self._end_date_btn, self._end_date, self._set_end_date)

    def _open_calendar(self, anchor: ctk.CTkButton, current: date | None, on_pick: Callable[[date], None]) -> None:
        if not self._state.has_data:
            return
        ts = self._state.timestamps
        min_d = ts[0].date()
        max_d = ts[-1].date()
        selected = current if current is not None else min_d
        _CalendarPopup(
            master=self.winfo_toplevel(),
            palette=self._palette,
            selected=selected,
            min_date=min_d,
            max_date=max_d,
            on_select=on_pick,
            anchor_widget=anchor,
        )

    def _set_start_date(self, d: date) -> None:
        self._start_date = d
        self._start_date_btn.configure(text=d.isoformat())
        self._on_change()

    def _set_end_date(self, d: date) -> None:
        self._end_date = d
        self._end_date_btn.configure(text=d.isoformat())
        self._on_change()

    # ---- change handling ----------------------------------------------- #

    def _on_change(self) -> None:
        if self._suppress_change or not self._state.has_data:
            return
        if self._start_date is None or self._end_date is None:
            return
        try:
            hh_s, mm_s = int(self._start_hh.get()), int(self._start_mm.get())
            hh_e, mm_e = int(self._end_hh.get()), int(self._end_mm.get())
        except ValueError:
            return

        start_dt = datetime.combine(self._start_date, time(hh_s % 24, mm_s % 60))
        end_dt = datetime.combine(self._end_date, time(hh_e % 24, mm_e % 60))

        swapped = end_dt < start_dt
        if swapped:
            start_dt, end_dt = end_dt, start_dt

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
            except tk.TclError:
                pass
        self._warning_after_id = self.after(3000, self._clear_warning)

    def _clear_warning(self) -> None:
        self._warning.configure(text="")
        self._warning_after_id = None
