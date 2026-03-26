from typing import Any


def empty_formatter(value: Any) -> str:
    """Return empty string for `None` value."""
    return ""


def bool_formatter(value: bool) -> str:
    """Return 'Yes' or 'No' string representation of a boolean value."""
    return "Yes" if value else "No"


BASE_FORMATTERS = {
    type(None): empty_formatter,
    bool: bool_formatter,
}
