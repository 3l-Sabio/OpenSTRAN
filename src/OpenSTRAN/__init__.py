"""OpenSTRAN - Open-source Structural Analysis Package.

A Python package for 3D finite element analysis of space frames.
This package provides tools for structural modeling and analysis.

Example:

    >>> from OpenSTRAN import Model
    >>> from OpenSTRAN import Shape
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("OpenSTRAN")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

from .Model import Model
from .Database.Shape import Shape

__all__ = ["Model", "Shape"]
