import pandas as pd
import plotnine as p9

from socviz_pl import theme_map, theme_socviz, theme_socviz_map, theme_socviz_semi


def test_socviz_themes_draw():
    plot = p9.ggplot(pd.DataFrame({"x": [1, 2], "y": [3, 4]}), p9.aes("x", "y")) + p9.geom_point()

    for theme in [theme_socviz(), theme_socviz_map(), theme_socviz_semi(), theme_map()]:
        (plot + theme).draw(show=False)


def test_socviz_theme_keeps_faint_panel_grid():
    theme = theme_socviz()

    major = theme.themeables["panel_grid_major"].theme_element.properties
    minor = theme.themeables["panel_grid_minor"].theme_element.properties

    assert major["color"] == "#E5E5E5"
    assert minor["color"] == "#E5E5E5"
    assert major["linewidth"] < 0.5
    assert minor["linewidth"] < major["linewidth"]
