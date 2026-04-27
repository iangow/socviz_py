from __future__ import annotations

_PREFERRED_FONTS = [
    "Roboto Condensed",
    "Fira Sans Condensed",
    "Helvetica Neue",
    "Arial",
]


def _resolve_font(preferred: str | None = None) -> str:
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    candidates = ([preferred] if preferred else []) + _PREFERRED_FONTS
    for name in candidates:
        if name in available:
            return name
    return "sans-serif"


def theme_socviz(
    base_size: int = 12,
    base_family: str | None = None,
    title_family: str | None = None,
):
    """Return a compact plotnine theme matching the Socviz book style."""

    import plotnine as p9

    base_family = _resolve_font(base_family)

    return (
        p9.theme_minimal(base_size=base_size, base_family=base_family)
        + p9.theme(
            text=p9.element_text(family=base_family),
            plot_background=p9.element_rect(fill="white", color=None),
            panel_background=p9.element_rect(fill="white", color=None),
            panel_grid_major=p9.element_line(color="#E5E5E5", size=0.2),
            panel_grid_minor=p9.element_line(color="#E5E5E5", size=0.15),
            dpi=100,
            figure_size=(6, 3.5),
        )
    )


def theme_socviz_map(
    base_size: int = 12,
    base_family: str = "Helvetica Neue",
    title_family: str | None = None,
):
    """Return a quiet plotnine map theme matching the Socviz book style."""

    import plotnine as p9

    return (
        theme_socviz(
            base_size=base_size,
            base_family=base_family,
            title_family=title_family,
        )
        + p9.theme(
            axis_line=p9.element_blank(),
            axis_text=p9.element_blank(),
            axis_ticks=p9.element_blank(),
            axis_title=p9.element_blank(),
            axis_text_x=p9.element_blank(),
            axis_text_y=p9.element_blank(),
            panel_background=p9.element_blank(),
            panel_border=p9.element_blank(),
            panel_grid=p9.element_blank(),
            panel_grid_major=p9.element_blank(),
            panel_grid_minor=p9.element_blank(),
            panel_spacing=0,
            plot_background=p9.element_blank(),
            plot_title=p9.element_text(ha="left"),
            legend_position="inside",
            legend_position_inside=(0, 0),
            legend_justification_inside=(0, 0),
        )
    )


def theme_socviz_semi(
    base_size: int = 12,
    base_family: str = "Helvetica Neue",
    title_family: str | None = None,
):
    """Alias for the book theme's SemiCondensed-style implementation."""

    return theme_socviz(
        base_size=base_size,
        base_family=base_family,
        title_family=title_family,
    )


def theme_map():
    """Backward-compatible alias for :func:`theme_socviz_map`."""

    return theme_socviz_map()
