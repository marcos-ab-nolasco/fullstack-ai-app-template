"""Expose project version to backend modules by reading the root VERSION file."""

from __future__ import annotations

from pathlib import Path


def _read_version_file() -> str:
    # Walk to repository root and read top-level VERSION file
    path = Path(__file__).resolve().parents[3] / "VERSION"
    if not path.exists():
        raise RuntimeError(f"VERSION file not found at expected path {path}")
    return path.read_text(encoding="utf-8").strip()


__version__ = _read_version_file()

__all__ = ["__version__"]
