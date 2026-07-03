"""Collection of handy utils written in Python 3."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chaos-utils")
except PackageNotFoundError:
    __version__ = "0.0.0"
