# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.filter
def extract_number_from_station_name(value):
    number_index = value.rfind('#')
    if number_index > -1:
        return value[number_index:]
    else:
        return value
