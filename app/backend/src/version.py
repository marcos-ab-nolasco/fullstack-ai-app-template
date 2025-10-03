"""Expose project version to backend modules."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_project_version() -> str:
    version_module = Path(__file__).resolve().parents[3] / "version.py"
    spec = importlib.util.spec_from_file_location("project_version", version_module)
    if spec is None or spec.loader is None:
        msg = f"Não foi possível carregar o módulo de versão em {version_module}"
        raise RuntimeError(msg)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    version_value = getattr(module, "__version__", None)
    if not isinstance(version_value, str):
        raise RuntimeError("__version__ não encontrado ou inválido em version.py")
    return version_value


__version__ = _load_project_version()

__all__ = ["__version__"]
