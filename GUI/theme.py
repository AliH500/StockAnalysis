"""
Dark + light palettes, font sizes, and a single helper that paints a
matplotlib axes to match. Pure data — no Tk widgets here.
"""

from __future__ import annotations

import matplotlib as mpl

# matplotlib reads the TTF's family name from its name table; for the
# Nunito-Medium static TTF that is "Nunito" (Medium is a weight, not part
# of the family). Use this constant everywhere so the font lookup matches.
FONT_FAMILY = "Nunito"

# Centralised type scale. Bumped from the original release so everything
# reads comfortably on a 1080p display.
FONT_SIZES = {
    "tiny": 12,
    "small": 14,
    "body": 16,
    "label": 17,
    "metric": 22,
    "section": 18,
    "title": 16,
    "tick": 12,
    "calendar_day": 14,
    "calendar_header": 16,
}

# Up / down colours used on the chart line and gradient when the current
# close is above / below the 7-day-ago close.
UP_GREEN = "#22C55E"
DOWN_RED = "#EF4444"
# RGBA tuples for the gradient under the line, parallel to the line colour.
UP_GRADIENT_TOP = (0.133, 0.773, 0.369, 0.55)
UP_GRADIENT_BOTTOM = (0.133, 0.773, 0.369, 0.00)
DOWN_GRADIENT_TOP = (0.937, 0.267, 0.267, 0.55)
DOWN_GRADIENT_BOTTOM = (0.937, 0.267, 0.267, 0.00)

DARK_PALETTE: dict = {
    "bg": "#0E1116",
    "panel_bg": "#161B22",
    "panel_border": "#222831",
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted": "#5C6772",
    "accent": "#58A6FF",
    "accent_muted": "#1F6FEB",
    "hover_bg": "#1E242C",
    "axes_bg": "#0E1116",
    "tick_color": "#8B949E",
    "grid_color": "#222831",
    "placeholder_text": "#5C6772",
    "spinbox_bg": "#161B22",
    "spinbox_fg": "#E6EDF3",
    "spinbox_button": "#222831",
    "error_text": "#F87171",
    "warning_text": "#FBBF24",
    "reference_line": "#3A4250",
}

LIGHT_PALETTE: dict = {
    "bg": "#F7F8FA",
    "panel_bg": "#FFFFFF",
    "panel_border": "#E5E7EB",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "accent": "#2563EB",
    "accent_muted": "#1D4ED8",
    "hover_bg": "#F1F5F9",
    "axes_bg": "#FFFFFF",
    "tick_color": "#64748B",
    "grid_color": "#E5E7EB",
    "placeholder_text": "#94A3B8",
    "spinbox_bg": "#FFFFFF",
    "spinbox_fg": "#0F172A",
    "spinbox_button": "#E5E7EB",
    "error_text": "#DC2626",
    "warning_text": "#D97706",
    "reference_line": "#CBD5E1",
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
        labelsize=FONT_SIZES["tick"],
    )
    ax.grid(True, color=palette["grid_color"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(palette["tick_color"])
        label.set_fontfamily(mpl.rcParams["font.family"])
