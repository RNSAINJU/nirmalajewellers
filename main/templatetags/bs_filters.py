from datetime import timezone, timedelta
from django import template

register = template.Library()

NPT = timezone(timedelta(hours=5, minutes=45), name='NPT')


try:
    # Prefer the real Nepali date conversion utilities if available.
    from common.nepali_utils import ad_to_bs_date_str, ad_to_bs_datetime_str  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback if helper module is missing
    def ad_to_bs_date_str(value):
        """Fallback: return a simple date string if Nepali utils are unavailable."""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def ad_to_bs_datetime_str(value):
        """Fallback: return a simple datetime string if Nepali utils are unavailable."""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M")
        return str(value)


@register.filter
def bs_date(value):
    return ad_to_bs_date_str(value)


@register.filter
def bs_datetime(value):
    return ad_to_bs_datetime_str(value)


@register.filter
def nepal_time(value):
    """Convert a datetime to Nepal Time (UTC+5:45) and format as 'YYYY-MM-DD HH:MM AM/PM'."""
    if not value:
        return ''
    try:
        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
            npt_dt = value.astimezone(NPT)
        else:
            npt_dt = value.replace(tzinfo=timezone.utc).astimezone(NPT)
        return npt_dt.strftime('%Y-%m-%d %I:%M %p')
    except Exception:
        return str(value)


@register.filter(name="split")
def split_filter(value, sep):
    """Split a string by the given separator.

    Usage in templates: "a,b,c"|split:"," -> ["a", "b", "c"].
    """
    if value is None:
        return []
    text = str(value)
    # Django templates sometimes pass an empty string as the separator,
    # e.g. "1234"|split:"" to iterate characters. Python's str.split("")
    # raises ValueError, so handle that case explicitly.
    if sep == "":
        return list(text)
    return text.split(sep)
