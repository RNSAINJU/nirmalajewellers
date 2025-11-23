import nepali_datetime as ndt
from datetime import date, datetime

NEPALI_MONTHS = [
    'Baisakh', 'Jestha', 'Asar', 'Shrawan', 'Bhadra', 'Ashwin',
    'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra'
]

def ad_to_bs_date_str(ad_date: date) -> str:
    """Return transliterated BS date string like '2082 Baisakh 01'."""
    if not ad_date:
        return ''
    try:
        bs = ndt.date.from_datetime_date(ad_date)
        return f"{bs.year} {NEPALI_MONTHS[bs.month - 1]} {bs.day:02d}"
    except (OverflowError, ValueError):
        return ''  # or return ad_date.isoformat()

def ad_to_bs_datetime_str(ad_dt: datetime) -> str:
    """Return transliterated BS datetime string or '' on failure."""
    if not ad_dt:
        return ''
    try:
        bs = ndt.datetime.from_datetime_datetime(ad_dt)
        return f"{bs.year} {NEPALI_MONTHS[bs.month - 1]} {bs.day:02d} {bs.hour:02d}:{bs.minute:02d}:{bs.second:02d}"
    except (OverflowError, ValueError):
        return ''