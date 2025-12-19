from django import template

register = template.Library()


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
