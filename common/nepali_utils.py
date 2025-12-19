"""Utilities to convert Gregorian (AD) dates to Nepali (BS) strings.

These helpers are used by template filters (bs_date / bs_datetime) so that
all dates can be rendered in Bikram Sambat as per the stored data.

They rely on the `nepali_datetime` package, which is already used
indirectly by `nepali_datetime_field.NepaliDateField` in this project.
If that package is not available at runtime, the functions gracefully
fall back to simple string formatting of the original value.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

try:  # Use the existing Nepali date implementation if available
    import nepali_datetime as ndt  # type: ignore[import]
except Exception:  # pragma: no cover - library presence depends on runtime env
    ndt = None  # type: ignore[assignment]


def _as_ad_date(value) -> Optional[date]:
    """Normalize various date-like inputs to a Python `date` where possible.

    - If value is a Python `datetime`, use its `.date()`.
    - If value is a Python `date`, use it as-is.
    - If value is already a Nepali date (`ndt.date`), return None so that
      the caller can treat it as BS and just format it directly.
    """
    if value is None:
        return None

    if ndt is not None and isinstance(value, getattr(ndt, "date", ())):
        # Already a Nepali BS date; let caller format it directly.
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return None


def ad_to_bs_date_str(value) -> str:
    """Convert an AD date/datetime to a BS date string (YYYY-MM-DD).

    If `value` is already a Nepali date instance, it is simply formatted.
    If the `nepali_datetime` package is not available, this falls back to
    `str(value)` so that templates still render something instead of failing.
    """
    if value is None:
        return ""

    # If we have nepali_datetime, prefer precise conversion
    if ndt is not None:
        nepali_date_type = getattr(ndt, "date", None)
        nepali_datetime_type = getattr(ndt, "datetime", None)

        # Already a Nepali date/datetime: just format
        if nepali_date_type is not None and isinstance(value, nepali_date_type):
            return value.strftime("%Y-%m-%d")
        if nepali_datetime_type is not None and isinstance(value, nepali_datetime_type):
            return value.strftime("%Y-%m-%d")

        # Convert Python date/datetime (AD) to Nepali BS date
        ad_date = _as_ad_date(value)
        if ad_date is not None and nepali_date_type is not None:
            try:
                bs_date = nepali_date_type.from_datetime_date(ad_date)
                return bs_date.strftime("%Y-%m-%d")
            except Exception:
                # If conversion fails for any reason, fall back to string
                return str(value)

    # Fallback: no nepali_datetime available; return a sensible string
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def ad_to_bs_datetime_str(value) -> str:
    """Convert an AD datetime to a BS datetime string (YYYY-MM-DD HH:MM).

    Behaves similarly to `ad_to_bs_date_str`, but includes the time portion.
    """
    if value is None:
        return ""

    if ndt is not None:
        nepali_date_type = getattr(ndt, "date", None)
        nepali_datetime_type = getattr(ndt, "datetime", None)

        # Already a Nepali datetime/date: just format
        if nepali_datetime_type is not None and isinstance(value, nepali_datetime_type):
            return value.strftime("%Y-%m-%d %H:%M")
        if nepali_date_type is not None and isinstance(value, nepali_date_type):
            # No time info; render midnight by convention
            return value.strftime("%Y-%m-%d 00:00")

        # Convert Python datetime/date to Nepali datetime
        if isinstance(value, datetime) and nepali_datetime_type is not None:
            try:
                bs_dt = nepali_datetime_type.from_datetime(value)
                return bs_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                return str(value)

        ad_date = _as_ad_date(value)
        if ad_date is not None and nepali_datetime_type is not None:
            try:
                ad_dt = datetime(ad_date.year, ad_date.month, ad_date.day)
                bs_dt = nepali_datetime_type.from_datetime(ad_dt)
                return bs_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                return str(value)

    # Fallback: no nepali_datetime; render a reasonable string
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d 00:00")
    if hasattr(value, "strftime"):
        # Any other date-like object with strftime
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value)
