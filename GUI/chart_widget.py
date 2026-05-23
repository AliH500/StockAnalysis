"""
Hero price chart: matplotlib `Figure` embedded in a CTkFrame, painted
with a vertical gradient fill under the line. Single redraw entrypoint
(`draw(palette)`); palette swaps are a full repaint, no widget recreation.
"""

from __future__ import annotations

import customtkinter as ctk
import matplotlib.dates as mdates
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app_state import AppState
from theme import apply_chart_style


class ChartWidget(ctk.CTkFrame):
    def __init__(self, parent, state: AppState, palette: dict):
        super().__init__(parent, fg_color=palette["bg"], corner_radius=12)
        self._state = state

        self._fig = Figure(figsize=(8, 4.5), dpi=100)
        self._fig.subplots_adjust(left=0.08, right=0.97, top=0.94, bottom=0.14)
        self._ax = self._fig.add_subplot(111)

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

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
                fontsize=16,
            )
            self._mpl_canvas.draw_idle()
            return

        timestamps = self._state.timestamps
        closes = self._state.closes
        x = mdates.date2num(timestamps)
        y = np.asarray(closes, dtype=float)

        (line,) = ax.plot(
            x, y, color=palette["chart_line"], linewidth=1.6, zorder=3
        )

        self._gradient_fill(ax, x, y, palette)

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
        ax.set_title(
            f"{self._state.series.ticker}  -  7-day, 1-minute  ({self._state.series.local_tz})",
            color=palette["text_primary"],
            fontsize=11,
            pad=10,
            loc="left",
        )
        self._mpl_canvas.draw_idle()

    def _gradient_fill(self, ax, x: np.ndarray, y: np.ndarray, palette: dict) -> None:
        """Vertical gradient under the price curve via `pcolormesh` + clip."""
        cmap = LinearSegmentedColormap.from_list(
            "price_gradient",
            [palette["gradient_bottom_rgba"], palette["gradient_top_rgba"]],
            N=256,
        )

        y_min = float(y.min())
        y_max = float(y.max())
        # Pad the vertical range slightly so the gradient and y-axis breathe.
        y_pad = (y_max - y_min) * 0.06 or 1.0
        y_lo = y_min - y_pad
        y_hi = y_max + y_pad

        ny = 256
        x_mesh = np.array([x[0], x[-1]])
        y_mesh = np.linspace(y_lo, y_hi, ny)
        z = np.linspace(0.0, 1.0, ny - 1).reshape(-1, 1)

        mesh = ax.pcolormesh(
            x_mesh, y_mesh, z, cmap=cmap, shading="flat", zorder=2
        )

        verts = list(zip(x, y))
        verts.append((x[-1], y_lo))
        verts.append((x[0], y_lo))
        clip_polygon = Polygon(verts, closed=True, transform=ax.transData)
        mesh.set_clip_path(clip_polygon)

        ax.set_ylim(y_lo, y_hi)
        ax.set_xlim(x[0], x[-1])
