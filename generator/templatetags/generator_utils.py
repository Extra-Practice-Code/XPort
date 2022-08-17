# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings

from generator.settings import SITE_URL as GENERATED_SITE_URL
from generator.links import is_link, is_multi_link, is_reverse_multi_link, is_reverse_single_link, is_single_link
from generator.collection import getObject

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


"""
@FIXME: making sorting optional
"""
@register.filter
def merged_targets (model):
  targets = []

  for field in model.fields.values():
    if is_multi_link(field) or is_reverse_multi_link(field):
      targets.extend(field.targets)
    elif is_single_link(field) or is_reverse_single_link(field):
      targets.append(field.target)

  return sorted(targets, key=lambda m: str(m).lower() if m else '')

@register.filter
def merged_links (model):
  links = []

  for field in model.fields.values():
    if is_multi_link(field) or is_reverse_multi_link(field):
      links.extend(field.links)
    elif is_single_link(field) or is_reverse_single_link(field):
      links.append(field.link)

  return links


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
def targets (links):
  return [link.target for link in links if link and link.resolved]

@register.filter
def without_inline_links (links, forbidden):
  if forbidden: 
    forbiddenContentTypes = list(map(str.strip, forbidden.split(',')))
    return list(filter(lambda l: l and l.resolved and not l.broken and not l.inline or (l and l.inline and l.target.contentType not in forbiddenContentTypes and l.source.contentType not in forbiddenContentTypes), links))
  else:
    return list(filter(lambda l: l and l.resolved and not l.broken and not l.inline, links))

@register.filter
def without (links, forbidden):
  forbiddenContentTypes = list(map(str.strip, forbidden.split(',')))
  return list(filter(lambda l: l and l.resolved and not l.broken and l.target.contentType not in forbiddenContentTypes and l.source.contentType not in forbiddenContentTypes, links))

@register.filter
def only (links, allowed):
  allowedContentTypes = list(map(str.strip, allowed.split(',')))
  return list(filter(lambda l: l and l.resolved and not l.broken and (l.target.contentType in allowedContentTypes or l.source.contentType in allowedContentTypes), links))

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


@register.simple_tag
def get_object (contentType, key):
  return getObject(contentType, key)


@register.simple_tag
def remove_inline_links (links, *forbiddenContentTypes):
  if forbiddenContentTypes:
    return list(filter(lambda l: not l.inline or (l.inline and l.target.contentType not in forbiddenContentTypes and l.source.contentType not in forbiddenContentTypes), links))
  else:
    return list(filter(lambda l: not l.inline, links))

from django.urls import reverse
from django.utils.http import urlencode

@register.simple_tag
def file_picker_url ():
  params = {}
  params['_pick'] = 'file'
  params['_popup'] = True
  
  return '{}?{}'.format(reverse('admin:filer-directory_listing-last'), urlencode(sorted(params.items())))
