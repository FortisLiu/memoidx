"""Stable identifiers for MemoIdx entities."""

from uuid import uuid4


def new_unit_id() -> str:
    """Generate a new stable unit identifier."""
    return f"u_{uuid4()}"


def new_file_id() -> str:
    """Generate a new stable file identifier."""
    return f"f_{uuid4()}"
