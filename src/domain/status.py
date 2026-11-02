"""A record's status over time: its current `status` began on `status_since`;
before that day it was active."""

from datetime import date
from typing import Any


def status_on(record: dict[str, Any], day: date) -> str:
    """The record's status on `day`: active before its current status began
    (`status_since`); the current status when that day is unknown."""
    since = record.get("status_since")
    return "active" if since is not None and day < since else record["status"]


def out_from(record: dict[str, Any]) -> date | None:
    """The day a record stopped being active (`status_since`); None while it is."""
    return None if record["status"] == "active" else record["status_since"]


def earliest(*days: date | None) -> date | None:
    """The first of the known days, or None."""
    known = [day for day in days if day is not None]
    return min(known) if known else None
