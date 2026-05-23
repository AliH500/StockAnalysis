"""
Top-level CTk window. Lays out the chart, both analytics panels, and the
range panel; owns the yfinance fetch lifecycle (daemon thread + queue +
`root.after` poll); owns the theme toggle.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
import matplotlib as mpl
from matplotlib import font_manager

from analytics_panel import AnalyticsPanel
from app_state import AppState
from chart_widget import ChartWidget
from data_loader import StockSeries, fetch_series
from range_panel import RangePanel
from theme import FONT_FAMILY, get_palette

POLL_INTERVAL_MS = 100
ERROR_AUTOCLEAR_MS = 5000
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "Nunito-Medium.ttf"


def _register_fonts() -> tuple[bool, bool]:
    """Returns (matplotlib_ok, tk_ok). Both degrade silently if False."""
    matplotlib_ok = False
    if FONT_PATH.exists():
        try:
            font_manager.fontManager.addfont(str(FONT_PATH))
            mpl.rcParams["font.family"] = FONT_FAMILY
            matplotlib_ok = True
        except Exception:
            pass

    tk_ok = False
    if FONT_PATH.exists():
        try:
            from tkextrafont import Font  # type: ignore
            Font(file=str(FONT_PATH), family=FONT_FAMILY)
            tk_ok = True
        except Exception:
            pass
    return matplotlib_ok, tk_ok


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        _register_fonts()

        self._mode = "dark"
        ctk.set_appearance_mode(self._mode)
        ctk.set_default_color_theme("blue")
        palette = get_palette(self._mode)

        self.title("Stock Analysis")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(fg_color=palette["bg"])

        self._state = AppState()
        self._fetch_queue: queue.Queue = queue.Queue()
        self._fetch_in_flight = False
        self._poll_after_id: str | None = None
        self._error_after_id: str | None = None

        self._build_layout(palette)
        self._apply_theme(palette)

    # ---- layout ----------------------------------------------------------

    def _build_layout(self, palette: dict) -> None:
        # Top bar: ticker entry + Load + spinner + theme toggle.
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            top,
            text="Ticker",
            font=(FONT_FAMILY, 13),
            text_color=palette["text_secondary"],
        ).pack(side="left", padx=(2, 8))

        self._ticker_entry = ctk.CTkEntry(
            top,
            width=140,
            font=(FONT_FAMILY, 13),
            placeholder_text="AAPL",
            border_color=palette["panel_border"],
            fg_color=palette["panel_bg"],
            text_color=palette["text_primary"],
        )
        self._ticker_entry.pack(side="left")
        self._ticker_entry.bind("<Return>", lambda _e: self._on_load_clicked())

        self._load_button = ctk.CTkButton(
            top,
            text="Load",
            width=88,
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_muted"],
            text_color="#FFFFFF",
            command=self._on_load_clicked,
        )
        self._load_button.pack(side="left", padx=(8, 12))

        self._spinner_label = ctk.CTkLabel(
            top,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=palette["text_secondary"],
        )
        self._spinner_label.pack(side="left")

        # Right side of top bar — theme toggle.
        self._theme_switch = ctk.CTkSwitch(
            top,
            text="Light mode",
            font=(FONT_FAMILY, 12),
            text_color=palette["text_secondary"],
            progress_color=palette["accent"],
            command=self._on_theme_toggle,
        )
        self._theme_switch.pack(side="right")

        # Inline error message (red).
        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=palette["error_text"],
            anchor="w",
        )
        self._error_label.pack(fill="x", padx=20, pady=(0, 4))

        # Main two-column body: chart left, side panels right.
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        body.grid_columnconfigure(0, weight=3, uniform="cols")
        body.grid_columnconfigure(1, weight=2, uniform="cols")
        body.grid_rowconfigure(0, weight=1)

        self._chart = ChartWidget(body, self._state, palette)
        self._chart.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        side = ctk.CTkFrame(body, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(0, weight=0)
        side.grid_rowconfigure(1, weight=0)
        side.grid_rowconfigure(2, weight=0)
        side.grid_rowconfigure(3, weight=1)

        self._week_panel = AnalyticsPanel(
            side, self._state, title="Full week", mode="week", palette=palette
        )
        self._week_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self._range_analytics = AnalyticsPanel(
            side, self._state, title="Selected range", mode="range", palette=palette
        )
        self._range_analytics.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self._range_panel = RangePanel(
            side,
            self._state,
            palette=palette,
            on_range_change=self._on_range_change,
        )
        self._range_panel.grid(row=2, column=0, sticky="ew")

    # ---- fetch lifecycle -------------------------------------------------

    def _on_load_clicked(self) -> None:
        if self._fetch_in_flight:
            return
        ticker = self._ticker_entry.get().strip().upper()
        if not ticker:
            self._show_error("Ticker cannot be empty.")
            return

        self._fetch_in_flight = True
        self._load_button.configure(state="disabled")
        self._spinner_label.configure(text=f"Fetching {ticker}...")
        self._clear_error()

        threading.Thread(
            target=self._fetch_worker,
            args=(ticker, self._fetch_queue),
            daemon=True,
        ).start()
        self._poll_after_id = self.after(POLL_INTERVAL_MS, self._poll_fetch)

    def _fetch_worker(self, ticker: str, result_queue: queue.Queue) -> None:
        try:
            series = fetch_series(ticker)
            result_queue.put(series)
        except Exception as exc:
            result_queue.put(exc)

    def _poll_fetch(self) -> None:
        try:
            result = self._fetch_queue.get_nowait()
        except queue.Empty:
            self._poll_after_id = self.after(POLL_INTERVAL_MS, self._poll_fetch)
            return

        self._poll_after_id = None
        self._fetch_in_flight = False
        self._spinner_label.configure(text="")
        self._load_button.configure(state="normal")

        if isinstance(result, Exception):
            self._show_error(f"Fetch failed: {result}")
            return

        assert isinstance(result, StockSeries)
        self._state.load(result)
        palette = get_palette(self._mode)
        self._chart.draw(palette)
        self._week_panel.refresh()
        self._range_panel.configure_bounds()
        self._range_analytics.refresh()

    # ---- theme toggle ----------------------------------------------------

    def _on_theme_toggle(self) -> None:
        self._mode = "light" if self._theme_switch.get() == 1 else "dark"
        ctk.set_appearance_mode(self._mode)
        palette = get_palette(self._mode)
        self._apply_theme(palette)

    def _apply_theme(self, palette: dict) -> None:
        self.configure(fg_color=palette["bg"])
        self._ticker_entry.configure(
            border_color=palette["panel_border"],
            fg_color=palette["panel_bg"],
            text_color=palette["text_primary"],
        )
        self._load_button.configure(
            fg_color=palette["accent"], hover_color=palette["accent_muted"]
        )
        self._spinner_label.configure(text_color=palette["text_secondary"])
        self._theme_switch.configure(
            text_color=palette["text_secondary"], progress_color=palette["accent"]
        )
        self._error_label.configure(text_color=palette["error_text"])
        self._chart.configure(fg_color=palette["bg"])
        self._week_panel.apply_theme(palette)
        self._range_analytics.apply_theme(palette)
        self._range_panel.apply_theme(palette)
        self._chart.draw(palette)

    # ---- range + error handling -----------------------------------------

    def _on_range_change(self) -> None:
        self._range_analytics.refresh()
        self._chart.draw(get_palette(self._mode))

    def _show_error(self, text: str) -> None:
        self._error_label.configure(text=text)
        if self._error_after_id is not None:
            try:
                self.after_cancel(self._error_after_id)
            except tk.TclError:
                pass
        self._error_after_id = self.after(ERROR_AUTOCLEAR_MS, self._clear_error)

    def _clear_error(self) -> None:
        self._error_label.configure(text="")
        self._error_after_id = None

    # ---- shutdown --------------------------------------------------------

    def destroy(self) -> None:
        for after_id in (self._poll_after_id, self._error_after_id):
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                except tk.TclError:
                    pass
        self._poll_after_id = None
        self._error_after_id = None
        super().destroy()
