"""
Hero price chart: matplotlib `Figure` embedded in a CTkFrame.

Line is coloured segment-by-segment — green where the close is above the
7-day-ago baseline, red where it is below. The gradient fill under the
line and the bottom-right trend chip use whichever of the two colours
matches the final close (overall trend). A horizontal reference line at
the 7-day-ago price makes the threshold visible at a glance.

`self._mpl_canvas` is named to avoid colliding with CTkFrame's own
internal `_canvas` attribute (used for rounded-corner drawing).
"""

from __future__ import annotations

import customtkinter as ctk
import matplotlib.dates as mdates
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app_state import AppState
from theme import (
    DOWN_GRADIENT_BOTTOM,
    DOWN_GRADIENT_TOP,
    DOWN_RED,
    FONT_SIZES,
    UP_GRADIENT_BOTTOM,
    UP_GRADIENT_TOP,
    UP_GREEN,
    apply_chart_style,
)


class ChartWidget(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, palette: dict):
        super().__init__(parent, fg_color=palette["bg"], corner_radius=14)
        self._state = state

        self._fig = Figure(figsize=(8, 4.8), dpi=100)
        self._fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.16)
        self._ax = self._fig.add_subplot(111)

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def draw(self, palette: dict) -> None:
        ax = self._ax
        ax.clear()

        if not self._state.has_data:
            apply_chart_style(ax, self._fig, palette)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0.5,
                0.5,
                "Enter a ticker to begin",
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=palette["placeholder_text"],
                fontsize=20,
            )
            self._mpl_canvas.draw_idle()
            return

        timestamps = self._state.timestamps
        closes = self._state.closes
        x = mdates.date2num(timestamps)
        y = np.asarray(closes, dtype=float)
        baseline = y[0]
        trending_up = y[-1] >= baseline

        gradient_top = UP_GRADIENT_TOP if trending_up else DOWN_GRADIENT_TOP
        gradient_bottom = UP_GRADIENT_BOTTOM if trending_up else DOWN_GRADIENT_BOTTOM
        self._gradient_fill(ax, x, y, gradient_top, gradient_bottom)

        # Per-segment colour: each segment is green if its midpoint sits
        # above the baseline, red if below.
        segments = np.stack([np.column_stack([x[:-1], y[:-1]]),
                             np.column_stack([x[1:], y[1:]])], axis=1)
        mids = (y[:-1] + y[1:]) / 2.0
        colors = np.where(mids >= baseline, UP_GREEN, DOWN_RED)
        line = LineCollection(segments, colors=colors, linewidth=2.0, zorder=4)
        ax.add_collection(line)

        # Reference line at the 7-day-ago baseline. zorder=3.5 puts it above
        # the gradient (zorder=3) but below the price line (zorder=4) so it
        # is clearly visible without competing with the line itself.
        ax.axhline(
            baseline,
            color=palette["reference_line"],
            linewidth=1.0,
            linestyle="--",
            alpha=0.85,
            zorder=3.5,
        )

        if self._state.range_l != self._state.range_r:
            ax.axvspan(
                x[self._state.range_l],
                x[self._state.range_r],
                color=palette["accent"],
                alpha=0.10,
                zorder=1,
            )

        apply_chart_style(ax, self._fig, palette)
        locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        trend_pct = (y[-1] - baseline) / baseline * 100 if baseline else 0
        trend_sign = "+" if trending_up else ""
        trend_color = UP_GREEN if trending_up else DOWN_RED
        ax.set_title(
            f"{self._state.series.ticker}   "
            f"${y[-1]:,.2f}   "
            f"{trend_sign}{trend_pct:.2f}%   "
            f"({self._state.series.local_tz})",
            color=trend_color,
            fontsize=FONT_SIZES["title"],
            pad=12,
            loc="left",
            fontweight="bold",
        )
        self._mpl_canvas.draw_idle()

    def _gradient_fill(
        self,
        ax,
        x: np.ndarray,
        y: np.ndarray,
        top_rgba: tuple,
        bottom_rgba: tuple,
    ) -> None:
        """Vertical gradient under the price curve via `pcolormesh` + clip."""
        cmap = LinearSegmentedColormap.from_list(
            "price_gradient", [bottom_rgba, top_rgba], N=256,
        )

        y_min = float(y.min())
        y_max = float(y.max())
        y_pad = (y_max - y_min) * 0.06 or 1.0
        y_lo = y_min - y_pad
        y_hi = y_max + y_pad

        ny = 256
        x_mesh = np.array([x[0], x[-1]])
        y_mesh = np.linspace(y_lo, y_hi, ny)
        z = np.linspace(0.0, 1.0, ny - 1).reshape(-1, 1)

        mesh = ax.pcolormesh(
            x_mesh, y_mesh, z, cmap=cmap, shading="flat", zorder=3,
        )

        verts = list(zip(x, y))
        verts.append((x[-1], y_lo))
        verts.append((x[0], y_lo))
        clip_polygon = Polygon(verts, closed=True, transform=ax.transData)
        mesh.set_clip_path(clip_polygon)

        ax.set_ylim(y_lo, y_hi)
        ax.set_xlim(x[0], x[-1])
