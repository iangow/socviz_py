from __future__ import annotations


def theme_socviz(
    base_size: int = 12,
    base_family: str = "Helvetica Neue",
    title_family: str | None = None,
):
    """Return a compact plotnine theme matching the Socviz book style."""

    import plotnine as p9

    title_family = title_family or base_family
    half_line = base_size / 2

    return (
        p9.theme_minimal(base_size=base_size, base_family=base_family)
        + p9.theme(
            line=p9.element_line(color="black", size=base_size / 24, lineend="butt"),
            rect=p9.element_rect(fill="white", color="black", size=base_size / 24),
            text=p9.element_text(
                family=base_family,
                color="black",
                size=base_size,
                linespacing=0.9,
            ),
            axis_line=p9.element_line(color="#1A1A1A", size=0.5),
            axis_text=p9.element_text(color="black", size=base_size * 1.3),
            axis_text_x=p9.element_text(margin={"t": 0.8 * half_line / 2}, va="top"),
            axis_text_y=p9.element_text(margin={"r": 0.8 * half_line / 2}, ha="right"),
            axis_ticks=p9.element_line(color="#1A1A1A"),
            axis_ticks_length=base_size / 4,
            axis_title=p9.element_text(size=base_size * 1.2),
            axis_title_x=p9.element_text(margin={"t": half_line / 2}, va="top"),
            axis_title_y=p9.element_text(
                rotation=90,
                margin={"r": half_line / 2},
                va="bottom",
            ),
            legend_background=p9.element_blank(),
            legend_key=p9.element_rect(fill="white", color=None),
            legend_key_size=1.2,
            legend_text=p9.element_text(size=base_size * 0.9),
            legend_title=p9.element_text(ha="left"),
            legend_position="top",
            legend_direction="horizontal",
            legend_box="horizontal",
            legend_justification="center",
            legend_box_background=p9.element_blank(),
            panel_background=p9.element_rect(fill="white", color=None),
            panel_border=p9.element_blank(),
            panel_grid=p9.element_line(color="#E5E5E5", size=0.1),
            panel_grid_major=p9.element_line(color="#E5E5E5", size=0.1),
            panel_grid_minor=p9.element_line(color="#E5E5E5", size=0.1),
            panel_spacing=half_line,
            strip_background=p9.element_blank(),
            strip_text=p9.element_text(
                color="#1A1A1A",
                size=base_size * 1.1,
                margin={
                    "t": 0.8 * half_line,
                    "r": 0.8 * half_line,
                    "b": 0.8 * half_line,
                    "l": 0.8 * half_line,
                },
            ),
            strip_text_y=p9.element_text(rotation=-90),
            plot_background=p9.element_rect(color="white"),
            plot_title=p9.element_text(
                family=title_family,
                weight="bold",
                size=base_size * 1.4,
                ha="left",
                va="top",
                margin={"b": half_line},
            ),
            plot_title_position="panel",
            plot_subtitle=p9.element_text(
                ha="left",
                va="top",
                size=base_size * 1.25,
                margin={"b": half_line},
            ),
            plot_caption=p9.element_text(
                size=base_size * 0.9,
                ha="right",
                va="top",
                margin={"t": half_line},
            ),
            plot_caption_position="panel",
            plot_tag=p9.element_text(size=base_size * 1.2),
            plot_tag_position="topleft",
            plot_margin=half_line,
            dpi=100,
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
