"""Expose project version to backend modules."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("backend")

__all__ = ["__version__"]
