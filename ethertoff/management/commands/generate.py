# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil


import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient
from .parse import parse_pads
from .models import collectionFor

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
    w.write(loader.render_to_string(template, context))


class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    outputdir = os.path.join(BASE_DIR, 'ethertoff', 'static', 'generated')

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.mkdir(outputdir)
    os.mkdir(os.path.join(outputdir, 'produsers'))
  
    print('Copying static files')

    shutil.copytree(os.path.join(BASE_DIR, 'ethertoff', 'templates', 'generated', 'static'), os.path.join(outputdir, 'static'))

    parse_pads()

    print('Read pads')
    print('Generating output')

    produsers = collectionFor('produser')
    events = collectionFor('event')

    # output(os.path.join(outputdir, 'produsers.html'), 'generated/produsers.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)) })
    output(os.path.join(outputdir, 'produsers.layout.html'), 'generated/produsers.layout.html', { 'produsers': produsers.models, key=lambda r: str(r.key)) })

    for produser in produsers.models:
      output(os.path.join(outputdir, 'produsers', '{}.html'.format(produser.key)), 'generated/produser.html', { 'produser': produser })

    output(os.path.join(outputdir, 'index.html'), 'generated/index.html', { 'events': sorted(filter(lambda obj: hasattr(obj, 'date'), events.models), key=lambda r: str(r.date), reverse=True) })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
