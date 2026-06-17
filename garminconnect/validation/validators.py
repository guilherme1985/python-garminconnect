"""Validation utilities for Garmin Connect API input parameters."""

import numbers
import re
from datetime import datetime

# Constants for validation
MAX_ACTIVITY_LIMIT = 1000
MAX_HYDRATION_ML = 10000  # 10 liters
DATE_FORMAT_REGEX = r"^\d{4}-\d{2}-\d{2}$"
DATE_FORMAT_STR = "%Y-%m-%d"
VALID_WEIGHT_UNITS = {"kg", "lbs"}


def validate_date_format(date_str: str, param_name: str = "date") -> str:
    """Validate date string format YYYY-MM-DD.

    Args:
        date_str: Date string to validate
        param_name: Parameter name for error messages

    Returns:
        Validated and stripped date string

    Raises:
        ValueError: If date format is invalid or date is impossible

    """
    if not isinstance(date_str, str):
        raise ValueError(f"{param_name} must be a string")

    date_str = date_str.strip()

    if not re.fullmatch(DATE_FORMAT_REGEX, date_str):
        raise ValueError(
            f"{param_name} must be in format 'YYYY-MM-DD', got: {date_str}"
        )

    try:
        datetime.strptime(date_str, DATE_FORMAT_STR)
    except ValueError as e:
        raise ValueError(f"invalid {param_name}: {e}") from e

    return date_str


def validate_positive_number(
    value: int | float, param_name: str = "value"
) -> int | float:
    """Validate that a number is positive.

    Args:
        value: Number to validate
        param_name: Parameter name for error messages

    Returns:
        Validated number

    Raises:
        ValueError: If value is not positive or not a number

    """
    if not isinstance(value, numbers.Real):
        raise ValueError(f"{param_name} must be a number")

    if isinstance(value, bool):
        raise ValueError(f"{param_name} must be a number, not bool")

    if value <= 0:
        raise ValueError(f"{param_name} must be positive, got: {value}")

    return value


def validate_non_negative_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a non-negative integer.

    Args:
        value: Integer to validate
        param_name: Parameter name for error messages

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not a non-negative integer

    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")

    if value < 0:
        raise ValueError(f"{param_name} must be non-negative, got: {value}")

    return value


def validate_positive_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a positive integer.

    Args:
        value: Integer to validate
        param_name: Parameter name for error messages

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not a positive integer

    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{param_name} must be a positive integer, got: {value}")
    return value


# Backward compatibility aliases (used by legacy code in __init__.py)
_validate_date_format = validate_date_format
_validate_positive_number = validate_positive_number
_validate_non_negative_integer = validate_non_negative_integer
_validate_positive_integer = validate_positive_integer
