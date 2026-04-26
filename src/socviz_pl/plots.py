from __future__ import annotations


def theme_map():
    """Return a quiet plotnine map theme matching the companion book."""

    import plotnine as p9

    return (
        p9.theme_void()
        + p9.theme(
            dpi=100,
            legend_position="bottom",
            plot_title=p9.element_text(ha="left", size=12),
            strip_background=p9.element_rect(fill="white", color="white"),
        )
    )
