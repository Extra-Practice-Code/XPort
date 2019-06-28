# -*- coding: utf-8 -*-

from .settings import SHOW_LOG_MESSAGES
from .settings import SHOW_DEBUG_MESSAGES

import re

CRED = '\033[91m'
CGREEN = '\033[92m'
CYELLOW = '\033[93m'
CMAGENTA = '\033[95m'
CCYAN = '\033[96m'
CEND = '\033[0m'

def info(*args):
  if SHOW_LOG_MESSAGES:
    print(*[str(a).encode('utf-8') for a in args])

def debug(*args, color=CCYAN):
  if SHOW_DEBUG_MESSAGES:
    print(color, *[str(a).encode('utf-8') for a in args], CEND)

def warn(*args):
  print(CYELLOW, *[str(a).encode('utf-8') for a in args], CEND)

def error(*args):
  print(CRED, *[str(a).encode('utf-8') for a in args], CEND)


def regroup (iterable, field):
  index = {}
  grouped = []
  
  for entry in iterable:
    try:
      key = getattr(entry, field)
    except AttributeError:
      key = ''

    if not key in index:
      grouped.append((key, [ entry ]))
      index[key] = grouped[-1]
    else:
      index[key][1].append(entry)

  return grouped


def try_attributes (obj, attributes):
  for attr in attributes:
    if hasattr(obj, attr):
      return getattr(obj, attr)
  
  return None


def keyFilter (value):
  if type(value) is list:
    return '--'.join([keyFilter(v) for v in value])
  elif type(value) is str:
    return re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', value.lower()))
  else: 
    return value