"""OpenSTRAN - Open-source Structural Analysis Package.

A Python package for 3D finite element analysis of space frames.
This package provides tools for structural modeling and analysis.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("OpenSTRAN")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
