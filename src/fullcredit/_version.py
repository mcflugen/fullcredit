from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

try:
    __version__ = version("fullcredit")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
