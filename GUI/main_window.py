"""
Top-level CTk window. Lays out the chart, both analytics panels, and the
range panel; owns the yfinance fetch lifecycle (daemon thread + queue +
`root.after` poll); owns the theme toggle.

Side-column order: Full week → Range query inputs → Selected range output.
(Inputs sit directly above the output they drive.)
"""

from __future__ import annotations

import queue
import sys
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
from theme import FONT_FAMILY, FONT_SIZES, get_palette

POLL_INTERVAL_MS = 100
ERROR_AUTOCLEAR_MS = 5000


def _resource_base() -> Path:
    """Where bundled assets live, whether running from source or a PyInstaller
    one-file executable. PyInstaller sets `sys._MEIPASS` to the temp extract
    dir; from source we resolve relative to this file."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


FONTS_DIR = _resource_base() / "fonts"
FONT_PATH = FONTS_DIR / "Nunito-Medium.ttf"  # kept for back-compat in error logs


def _register_fonts() -> tuple[bool, bool]:
    """Make every bundled Nunito weight available to both matplotlib and Tk.

    Returns (matplotlib_ok, tk_ok). Warnings are written to stderr so they
    show up in the user's terminal when something silently degrades.

    On Windows the Tk-side load uses the Win32 GDI `AddFontResourceExW`
    with `FR_PRIVATE`, which registers the font into the current process
    only — no admin rights, no extra C extension. `tkextrafont` is tried
    as a fallback for Linux / macOS, but is no longer required for the
    Windows executable to render correctly.
    """
    matplotlib_ok = False
    if FONTS_DIR.is_dir():
        registered = 0
        for ttf in sorted(FONTS_DIR.glob("Nunito-*.ttf")):
            try:
                font_manager.fontManager.addfont(str(ttf))
                registered += 1
            except Exception as exc:
                print(f"[font] matplotlib could not load {ttf.name}: {exc}", file=sys.stderr)
        if registered:
            mpl.rcParams["font.family"] = FONT_FAMILY
            matplotlib_ok = True

    tk_ok = _register_tk_fonts_win32() or _register_tk_fonts_extrafont()
    if not tk_ok and FONTS_DIR.is_dir():
        print(
            f"[font] {FONT_FAMILY} could not be loaded into Tk; "
            f"widgets will fall back to a system font. "
            f"On Windows this should never happen; on Linux/macOS install "
            f"`tkextrafont` (or the Nunito font system-wide) to fix.",
            file=sys.stderr,
        )
    return matplotlib_ok, tk_ok


def _register_tk_fonts_win32() -> bool:
    """Win32 AddFontResourceExW — Windows only, no third-party deps.
    Loads every Nunito-*.ttf bundled in `FONTS_DIR` into the current process."""
    if sys.platform != "win32" or not FONTS_DIR.is_dir():
        return False
    try:
        import ctypes
        FR_PRIVATE = 0x10
        registered = 0
        for ttf in sorted(FONTS_DIR.glob("Nunito-*.ttf")):
            result = ctypes.windll.gdi32.AddFontResourceExW(str(ttf), FR_PRIVATE, 0)
            if result > 0:
                registered += 1
            else:
                print(f"[font] AddFontResourceExW failed for {ttf.name}", file=sys.stderr)
        return registered > 0
    except Exception as exc:
        print(f"[font] Win32 font registration errored: {exc}", file=sys.stderr)
        return False


def _register_tk_fonts_extrafont() -> bool:
    """Cross-platform fallback using the tkextrafont C extension."""
    if not FONTS_DIR.is_dir():
        return False
    try:
        from tkextrafont import Font  # type: ignore
    except Exception:
        return False
    registered = 0
    for ttf in sorted(FONTS_DIR.glob("Nunito-*.ttf")):
        try:
            Font(file=str(ttf))
            registered += 1
        except Exception as exc:
            print(f"[font] tkextrafont could not load {ttf.name}: {exc}", file=sys.stderr)
    return registered > 0


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        _register_fonts()

        self._mode = "light"
        ctk.set_appearance_mode(self._mode)
        ctk.set_default_color_theme("blue")
        palette = get_palette(self._mode)

        self.title("Stock Analysis")
        self.geometry("1440x880")
        self.minsize(1200, 760)
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
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(
            top,
            text="Ticker",
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            text_color=palette["text_secondary"],
        ).pack(side="left", padx=(2, 10))

        self._ticker_entry = ctk.CTkEntry(
            top,
            width=180,
            height=40,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            placeholder_text="AAPL",
            border_color=palette["panel_border"],
            fg_color=palette["panel_bg"],
            text_color=palette["text_primary"],
            corner_radius=8,
        )
        self._ticker_entry.pack(side="left")
        self._ticker_entry.bind("<Return>", lambda _e: self._on_load_clicked())

        self._load_button = ctk.CTkButton(
            top,
            text="Load",
            width=110,
            height=40,
            font=(FONT_FAMILY, FONT_SIZES["body"], "bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_muted"],
            text_color="#FFFFFF",
            corner_radius=8,
            command=self._on_load_clicked,
        )
        self._load_button.pack(side="left", padx=(10, 16))

        self._spinner_label = ctk.CTkLabel(
            top,
            text="",
            font=(FONT_FAMILY, FONT_SIZES["small"]),
            text_color=palette["text_secondary"],
        )
        self._spinner_label.pack(side="left")

        self._theme_switch = ctk.CTkSwitch(
            top,
            text="Light mode",
            font=(FONT_FAMILY, FONT_SIZES["small"]),
            text_color=palette["text_secondary"],
            progress_color=palette["accent"],
            command=self._on_theme_toggle,
        )
        self._theme_switch.pack(side="right")
        # Default mode is light → switch starts in the ON position.
        self._theme_switch.select()

        # Inline error message (red).
        self._error_label = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, FONT_SIZES["small"]),
            text_color=palette["error_text"],
            anchor="w",
        )
        self._error_label.pack(fill="x", padx=24, pady=(0, 6))

        # Main two-column body: chart left, side panels right.
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(4, 20))

        body.grid_columnconfigure(0, weight=3, uniform="cols")
        body.grid_columnconfigure(1, weight=2, uniform="cols")
        body.grid_rowconfigure(0, weight=1)

        self._chart = ChartWidget(body, self._state, palette)
        self._chart.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        # Scrollable side column — guarantees the three panels are always
        # fully reachable regardless of window height.
        # Note: an explicit `fg_color` (not "transparent") is required so the
        # inner scroll canvas repaints when the theme toggles. CTk's
        # `transparent` propagation does not always reach the scrollable
        # frame's internal canvas, leaving a stale light bg in dark mode.
        self._side = ctk.CTkScrollableFrame(
            body,
            fg_color=palette["bg"],
            scrollbar_button_color=palette["panel_border"],
            scrollbar_button_hover_color=palette["accent"],
        )
        self._side.grid(row=0, column=1, sticky="nsew")
        self._side.grid_columnconfigure(0, weight=1)

        # Order: Full week → Range query inputs → Selected range output.
        self._week_panel = AnalyticsPanel(
            self._side, self._state, title="Full week", mode="week", palette=palette
        )
        self._week_panel.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._range_panel = RangePanel(
            self._side,
            self._state,
            palette=palette,
            on_range_change=self._on_range_change,
        )
        self._range_panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self._range_analytics = AnalyticsPanel(
            self._side, self._state, title="Selected range", mode="range", palette=palette
        )
        self._range_analytics.grid(row=2, column=0, sticky="ew", pady=(0, 12))

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
        self._side.configure(
            fg_color=palette["bg"],
            scrollbar_button_color=palette["panel_border"],
            scrollbar_button_hover_color=palette["accent"],
        )
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
