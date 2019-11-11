# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings

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

