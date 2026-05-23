"""
Dark + light palettes and a single helper that paints a matplotlib axes
to match. Pure data — no Tk widgets here.
"""

from __future__ import annotations

import matplotlib as mpl

# matplotlib reads the TTF's family name from its name table; for the
# Nunito-Medium static TTF that is "Nunito" (Medium is a weight, not part
# of the family). Use this constant everywhere so the font lookup matches.
FONT_FAMILY = "Nunito"

DARK_PALETTE: dict = {
    "bg": "#0E1116",
    "panel_bg": "#161B22",
    "panel_border": "#222831",
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "accent": "#58A6FF",
    "accent_muted": "#1F6FEB",
    "chart_line": "#58A6FF",
    # RGBA tuples on a 0-1 scale for matplotlib's colormap construction.
    "gradient_top_rgba": (0.345, 0.651, 1.000, 0.55),
    "gradient_bottom_rgba": (0.345, 0.651, 1.000, 0.00),
    "axes_bg": "#0E1116",
    "tick_color": "#8B949E",
    "grid_color": "#222831",
    "placeholder_text": "#5C6772",
    "spinbox_bg": "#161B22",
    "spinbox_fg": "#E6EDF3",
    "spinbox_button": "#222831",
    "error_text": "#F87171",
    "warning_text": "#FBBF24",
}

LIGHT_PALETTE: dict = {
    "bg": "#F7F8FA",
    "panel_bg": "#FFFFFF",
    "panel_border": "#E5E7EB",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "accent": "#2563EB",
    "accent_muted": "#1D4ED8",
    "chart_line": "#2563EB",
    "gradient_top_rgba": (0.145, 0.388, 0.922, 0.45),
    "gradient_bottom_rgba": (0.145, 0.388, 0.922, 0.00),
    "axes_bg": "#FFFFFF",
    "tick_color": "#64748B",
    "grid_color": "#E5E7EB",
    "placeholder_text": "#94A3B8",
    "spinbox_bg": "#FFFFFF",
    "spinbox_fg": "#0F172A",
    "spinbox_button": "#E5E7EB",
    "error_text": "#DC2626",
    "warning_text": "#D97706",
}


def get_palette(mode: str) -> dict:
    return DARK_PALETTE if mode == "dark" else LIGHT_PALETTE


def apply_chart_style(ax, fig, palette: dict) -> None:
    """Repaint axes + figure colours and gridlines to match `palette`."""
    fig.set_facecolor(palette["bg"])
    ax.set_facecolor(palette["axes_bg"])
    for spine in ax.spines.values():
        spine.set_color(palette["panel_border"])
    ax.tick_params(
        axis="both",
        colors=palette["tick_color"],
        labelsize=9,
    )
    ax.grid(True, color=palette["grid_color"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    # Set font on existing text artists. rcParams is set globally at app
    # init; this catches axes-local labels that may have been created
    # before the font was registered.
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(palette["tick_color"])
        label.set_fontfamily(mpl.rcParams["font.family"])
