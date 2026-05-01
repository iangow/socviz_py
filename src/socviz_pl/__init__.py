"""Polars-oriented API for the socviz_py package."""

from __future__ import annotations

from importlib import import_module

__version__ = "0.0.4"

__all__ = [
    "available_data",
    "data_path",
    "get_county_boundaries",
    "load_data",
    "theme_map",
    "theme_socviz",
    "theme_socviz_map",
    "theme_socviz_semi",
    "__version__",
]

_LAZY_IMPORTS = {
    "available_data": (".data", "available_data"),
    "data_path": (".data", "data_path"),
    "get_county_boundaries": (".data", "get_county_boundaries"),
    "load_data": (".data", "load_data"),
    "theme_map": (".plots", "theme_map"),
    "theme_socviz": (".plots", "theme_socviz"),
    "theme_socviz_map": (".plots", "theme_socviz_map"),
    "theme_socviz_semi": (".plots", "theme_socviz_semi"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_name, attr = _LAZY_IMPORTS[name]
        module = import_module(module_name, __name__)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
