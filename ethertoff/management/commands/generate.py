# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil

from math import inf


import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient
from .parse import parse_pads
from .models import collectionFor
from .utils import info

from django.template import loader
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from etherpadlite.models import Pad

from ethertoff.settings import PAD_NAMESPACE_SEPARATOR, BASE_DIR, DEBUG

FIELD_SINGLE = 'FIELD_SINGLE'
FIELD_ITERABLE = 'FIELD_ITERABLE'

FIELD_DATE_FORMAT = '%d-%m-%Y'
FIELD_DATETIME_FORMAT = '%d-%m-%Y %H:%M'
FIELD_TIME_FORMAT = '%H:%M'

import datetime


# List pads
# Go through them, record information
# Feed content to templates

def output (path, template, context):
  with open(path, 'w', encoding='utf-8') as w:
    info('Writing {} → {}'.format(template, path))
    w.write(loader.render_to_string(template, context))


produser_role_sorting = ['artist', 'co-producer', 'other professional', 'team', ' qpartner']

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
  
  return ''

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    outputdir = os.path.join(BASE_DIR, 'ethertoff', 'static', 'generated')

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.mkdir(outputdir)
    os.mkdir(os.path.join(outputdir, 'produsers'))
    os.mkdir(os.path.join(outputdir, 'events'))
  
    info('Copying static files')

    shutil.copytree(os.path.join(BASE_DIR, 'ethertoff', 'templates', 'generated', 'static'), os.path.join(outputdir, 'static'))

    parse_pads()

    info('Read pads')
    info('Generating output')

    produsers = collectionFor('produser')
    events = collectionFor('event')


    grouped_produsers = sorted(regroup(sorted(produsers.models, key=lambda produser: try_attributes(produser, ['name', 'produser'])), 'role'), key=lambda group: produser_role_sorting.index(group[0]) if group[0] in produser_role_sorting else inf)

    output(os.path.join(outputdir, 'produsers.html'), 'generated/produsers.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers })
    output(os.path.join(outputdir, 'produsers.layout.html'), 'generated/produsers.layout.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers  })

    for produser in produsers.models:
      output(os.path.join(outputdir, produser.prefix, '{}.html'.format(produser.key)), 'generated/produser.html', { 'produser': produser })

    for event in events.models:
      output(os.path.join(outputdir, event.prefix, '{}.html'.format(event.key)), 'generated/event.html', { 'event': event })

    output(os.path.join(outputdir, 'index.html'), 'generated/index.html', { 'events': sorted(events.models, key=lambda event: try_attributes(event, ['date']), reverse=True) })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
