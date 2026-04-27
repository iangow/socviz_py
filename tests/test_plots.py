import pandas as pd
import plotnine as p9

from socviz_pl import theme_map, theme_socviz, theme_socviz_map, theme_socviz_semi


def test_socviz_themes_draw():
    plot = p9.ggplot(pd.DataFrame({"x": [1, 2], "y": [3, 4]}), p9.aes("x", "y")) + p9.geom_point()

    for theme in [theme_socviz(), theme_socviz_map(), theme_socviz_semi(), theme_map()]:
        (plot + theme).draw(show=False)
