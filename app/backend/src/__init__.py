from src.core.local_logging import configure_logging

from .version import __version__

configure_logging()

__all__ = ["__version__"]
