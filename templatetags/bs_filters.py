from django import template
from common.nepali_utils import ad_to_bs_date_str, ad_to_bs_datetime_str

register = template.Library()

@register.filter
def bs_date(value):
    return ad_to_bs_date_str(value)

@register.filter
def bs_datetime(value):
    return ad_to_bs_datetime_str(value)