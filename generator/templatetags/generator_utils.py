# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings

from generator.settings import SITE_URL as GENERATED_SITE_URL
from generator.links import is_link, is_multi_link, is_reverse_multi_link, is_reverse_single_link, is_single_link

import re
import os.path

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
def merged_links (model):
  values = []

  for field in model.fields.values():
    if is_multi_link(field) or is_reverse_multi_link(field):
      values.extend(field.targets)
    elif is_single_link(field) or is_reverse_single_link(field):
      values.append(field.target)

  return sorted(values, key=lambda m: str(m).lower() if m else '')

@register.filter
def unwrap_galleries (models):
  unwrapped = []

  for model in models:
    if model:
      if model.contentType == 'gallery':
        unwrapped.extend(model.images.targets)
      else:
        unwrapped.append(model)

  return unwrapped

@register.filter
def without_inline_links (field):
  return list(filter(lambda l: not l.inline, field))

from random import shuffle
@register.filter
def shuffle_items (value):
    shuffle(value)
    return value


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


@register.simple_tag
def generated_site_url ():
  return os.path.join(GENERATED_SITE_URL, 'index.html')

@register.simple_tag
def generated_site_debug_url ():
  return os.path.join(GENERATED_SITE_URL, 'debug.html')

from django.urls import reverse
from django.utils.http import urlencode

@register.simple_tag
def file_picker_url ():
  params = {}
  params['_pick'] = 'file'
  params['_popup'] = True
  
  return '{}?{}'.format(reverse('admin:filer-directory_listing-last'), urlencode(sorted(params.items())))
