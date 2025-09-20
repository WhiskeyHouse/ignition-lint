"""
Ignition Lint - FastMCP server for Ignition empirical linting.

Provides production-validated quality checks for Ignition projects through
the Model Context Protocol (MCP) and naming convention validation.
"""

__version__ = "1.0.0"
__author__ = "Whiskey House Engineering & Technology"
__email__ = "pmannionwhiskeyhouse.com"

from .style_checker import StyleChecker
from .json_linter import JsonLinter

__all__ = ["StyleChecker", "JsonLinter"]

# Optional FastMCP server import
try:
    from .server import FastMCPIgnitionLinter
    __all__.append("FastMCPIgnitionLinter")
except ImportError:
    # FastMCP not available, that's okay for CLI usage
    pass
