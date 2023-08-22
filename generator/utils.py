# -*- coding: utf-8 -*-

from generator.settings import SHOW_LOG_MESSAGES
from generator.settings import SHOW_DEBUG_MESSAGES

from django.template import loader

import re
import random
from string import ascii_letters, digits

CRED = '\033[91m'
CGREEN = '\033[92m'
CYELLOW = '\033[93m'
CMAGENTA = '\033[95m'
CCYAN = '\033[96m'
CEND = '\033[0m'

def print_in_color(*messages, color=CEND):
  messages = ' '.join(map(str, messages))
  print('{}{}{}'.format(color, messages, CEND))

def info(*messages):
  if SHOW_LOG_MESSAGES:
    print(' '.join(map(str, messages)))

def debug(*messages, color=CCYAN):
  if SHOW_DEBUG_MESSAGES:
    print_in_color(*messages, color=color)

def warn(*messages):
  print_in_color(*messages, color=CYELLOW)

def error(*messages):
  print_in_color(*messages, color=CRED)


def regroup (iterable, key):
  index = {}
  grouped = []
  
  for model in iterable:
    if callable(key):
      groupkey = key(model)
    elif hasattr(model, key):
      groupkey = str(getattr(model, key))
    else:
      groupkey = ''

    if not groupkey in index:
      grouped.append((groupkey, [ model ]))
      index[groupkey] = grouped[-1]
    else:
      index[groupkey][1].append(model)

  return grouped


def try_attributes (obj, attributes):
  for attr in attributes:
    if hasattr(obj, attr) and getattr(obj, attr).value:
      return getattr(obj, attr)
  
  return None


def keyFilter (value):
  if type(value) is list:
    return '--'.join([keyFilter(str(v).lower().strip()) for v in filter(None, value)])
  elif type(value) is int:
    return str(value)
  else: 
    return re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', str(value).lower().strip()))


def render_template_to_string(template, context):
  return loader.render_to_string(template, context)


def make_id (length=15): 
  tokens = ascii_letters + digits
  return ''.join([random.choice(tokens) for _ in range(length)])


from bs4 import BeautifulSoup
# @FIXME rename to 'strip_tags' or 'remove_tags' feels more fiting
# for what it does?
def drop_tags (snippet, tags_to_drop=[]):
  soup = BeautifulSoup(snippet, 'html.parser')

  for tag in tags_to_drop:
    for element in soup.select(tag):
      element.decompose()

  return str(soup)
