"""
Ignition Lint - FastMCP server for Ignition empirical linting.

Provides production-validated quality checks for Ignition projects through
the Model Context Protocol (MCP) and naming convention validation.
"""

try:
    from ._version import __version__
except ModuleNotFoundError:  # editable install without build
    __version__ = "0.0.0.dev0"

__author__ = "Whiskey House Engineering & Technology"
__email__ = "pmannionwhiskeyhouse.com"

from .style_checker import StyleChecker
from .json_linter import JsonLinter

__all__ = ["StyleChecker", "JsonLinter"]
