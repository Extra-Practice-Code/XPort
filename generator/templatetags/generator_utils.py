# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings

import re

register = template.Library()

# @register.filter
# def sorted_images(project):
#   return project.images.all().order_by('projectimage__image_order')

# loop through the multilink field
# for each row return the link, the source, the target
@register.filter
def link_iterator (field):
  for link in field:
    if link:
      yield (link, link.source, link.target)

@register.filter
def link_target_iterator (field):
  for link in field:
    if link:
      yield link.target

@register.filter
def cut_from_start (value, arg):
  print(value)
  print('should be removed', arg)
  return re.sub('^' + str(arg), '', re.I)



@register.filter
def without_inline_links (field):
  return list(filter(lambda l: not l.inline, field))

@register.simple_tag
def combine_linkfields (*fields):
  combined = []
  targets = []

  for field in fields:
    if field:
      for link in field:
        if link.target not in targets:
          combined.append(link)
          targets.append(link.target)

  return combined