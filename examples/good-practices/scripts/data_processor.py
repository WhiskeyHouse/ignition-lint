"""Data processing utilities for manufacturing metrics.

This module provides functions for reading and processing production data
from Ignition tag system.
"""

import system.tag
import system.util


def read_production_count(line_number):
    """Read current production count for a manufacturing line.

    Args:
        line_number (int): Production line number (1-5)

    Returns:
        int: Current production count, or -1 on error

    Example:
        >>> count = read_production_count(1)
        >>> if count >= 0:
        ...     system.perspective.print(f"Line 1: {count} units")
    """
    try:
        tag_path = f"[default]Line{line_number}/ProductionCount"
        result = system.tag.readBlocking([tag_path])

        if result and result[0].quality.isGood():
            return result[0].value
        else:
            logger = system.util.getLogger("DataProcessor")
            logger.warn(f"Bad quality for line {line_number}")
            return -1

    except Exception as e:
        logger = system.util.getLogger("DataProcessor")
        logger.error(f"Failed to read production count: {e}")
        return -1


def calculate_efficiency(actual_count, target_count):
    """Calculate production efficiency percentage.

    Args:
        actual_count (int): Actual production count
        target_count (int): Target production count

    Returns:
        float: Efficiency percentage (0-100)
    """
    if target_count <= 0:
        return 0.0

    efficiency = (float(actual_count) / target_count) * 100
    return min(efficiency, 100.0)
