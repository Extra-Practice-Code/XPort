# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag('svg_icons/pause.svg')
def svg_icon_pause (**kwargs):
  return {
    'class': kwargs['class'] if 'class' in kwargs else 'button--label-pause button--label',
    'id': kwargs['id'] if 'id' in kwargs else '',
    'alt': kwargs['alt'] if 'alt' in kwargs else 'pause'
  }

@register.inclusion_tag('svg_icons/play.svg')
def svg_icon_play (**kwargs):
  return {
    'class': kwargs['class'] if 'class' in kwargs else 'button--label-play button--label',
    'id': kwargs['id'] if 'id' in kwargs else '',
    'alt': kwargs['alt'] if 'alt' in kwargs else 'play'
  }