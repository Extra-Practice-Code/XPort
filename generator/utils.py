# -*- coding: utf-8 -*-

from generator.settings import SHOW_DEBUG_MESSAGES, SHOW_LOG_MESSAGES, KEY_MAX_LENGTH

from django.template import loader

import re
import random
from string import ascii_letters, digits

from django.conf import settings
import os.path
import json

from ethertoff.utils import discoverFolders, pathToSlug, getPadBySlug

import unicodedata

PUBLICATION_INDEX_PATH = os.path.join(settings.BACKUP_DIR, 'index-publications.json')

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


def replaceEmojiiWithTheirName (value):
  # https://stackoverflow.com/a/32988437
  # Replace chars within a range for their name as found in the Unicode Character Database
  # Extended range to also include "Miscellaneous Symbols and Pictographs" and "Symbols and Pictographs Extended-A"
  # \U00000021 "Exclamation mark"
  # \U0000002B "Plus sign"
  # \U0000003F "Question mark"
  # \U00002700-\U000027BF "Dingbats"
  # \U0001F300-\U0001F5FF "Miscellaneous Symbols and Pictographs"
  # \U0001F600-\U0001F64F "Emoticons (Emoji)"
  # \U0001FA70-\U0001FAFF "Symbols and Pictographs Extended-A"
  # \U0001F900-\U0001F9FF "Supplemental Symbols and Pictographs"
  return re.sub('[\U00000021\U0000002B\U0000003F\U00002700-\U000027BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001FA70-\U0001FAFF\U0001F900-\U0001F9FF]', lambda m: unicodedata.name(m.group(0)), value)

"""
 Limit length of keys on models and replace characters
"""
def keyFilter (value):
  if type(value) is list:
    return '--'.join([keyFilter(str(v).lower().strip()) for v in filter(None, value)])[:KEY_MAX_LENGTH]
  elif type(value) is int:
    return str(value)
  else: 
    return re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', replaceEmojiiWithTheirName(str(value)).lower().strip()))[:KEY_MAX_LENGTH]


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


# [{ title: str, path: str, url: str }, ...]
def storePublications (organisation_slug, organisation_publications):
  publications = loadPublications()
  publications[organisation_slug] = organisation_publications

  json.dump(publications, open(PUBLICATION_INDEX_PATH, 'w'), ensure_ascii=False)


# [{ title: str, path: str, url: str }, ...]
def loadPublications ():
  try:
    publications = json.load(open(PUBLICATION_INDEX_PATH, 'r'))
  except IOError:
    publications = {}

  return publications

def discoverPublicationFolders (organisation_slug):
  return list(filter(lambda f: f not in settings.GENERATOR_SYSTEM_FOLDERS, discoverFolders([ organisation_slug ])))


def discoverThemeResourcePad (organisation_slug, publication, resource_name, theme=None):
  candidates = [
    # Try to find in publication
    pathToSlug([ organisation_slug, publication, settings.THEME_LOCAL_FOLDERNAME, resource_name]),
    # Otherwise in theme, if it is set, or in default
    pathToSlug([ organisation_slug, settings.THEMES_FOLDERNAME, theme, resource_name ]) if theme else pathToSlug(settings.THEME_DEFAULT_PATH + [ resource_name ]),
  ]

  print(candidates)

  for slug in candidates:
    pad = getPadBySlug(slug)

    if pad:
      return pad
    
  return None