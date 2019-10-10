# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings 


register = template.Library()

@register.filter(name='dewikify')
@stringfilter
def dewikify(name):
    name = name.replace('-', ' ')
    name = name.replace(settings.PAD_NAMESPACE_SEPARATOR, settings.PAD_NAMESPACE_SEPARATOR_DISPLAY)
    return name

@register.filter
def wikifyPath(value):
    return value.replace('/', settings.PAD_NAMESPACE_SEPARATOR)

@register.filter
def stripPath(value, path):
    if path is not None and len(path) > 0:
        from django.conf import settings
        PNS = settings.PAD_NAMESPACE_SEPARATOR
        pathstring = '{}{}'.format(PNS.join(path), PNS)
        return value.replace(pathstring, '')
    
    return value

@register.filter
def addPath(value, path):
    return '{}{}'.format(ensureTrailingSlash(pathString(path)), value)

@register.filter   
def pathString(path):
    if path is not None and len(path) > 0:
        return '{}'.format('/'.join(path))
    return ''

def ensureTrailingSlash(path):
    if len(path) > 0:
        if path[-1] != '/':
            return '{}/'.format(path)
    return path
