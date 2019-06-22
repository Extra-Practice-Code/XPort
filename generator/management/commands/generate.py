# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil

from math import inf


import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient
from generator.parse import parse_pads
from generator.models import collectionFor
from generator.utils import info, regroup, try_attributes

from django.template import loader
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from etherpadlite.models import Pad 

from ethertoff.settings import PAD_NAMESPACE_SEPARATOR, BASE_DIR, DEBUG
from generator.settings import SITE_URL, MENU_ITEMS

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
  context['SITE_URL'] = SITE_URL
  context['MENU_ITEMS'] = MENU_ITEMS
  
  with open(path, 'w', encoding='utf-8') as w:
    info('Writing {} -> {}'.format(template, path))
    w.write(loader.render_to_string(template, context))

def generate_single_pages (collection, template, outputdir, make_context):
  for model in collection.models:
    output(os.path.join(outputdir, model.prefix, '{}.html'.format(model.key)), template, make_context(model))

produser_role_sorting = ['artist', 'co-producer', 'other professional', 'team', ' qpartner']

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    basedir = os.path.join(BASE_DIR, 'generator')
    staticdir = os.path.join(basedir, 'templates', 'static')
    outputdir = os.path.join(basedir, 'static', 'generated')

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.mkdir(outputdir)
    os.mkdir(os.path.join(outputdir, 'produsers'))
    os.mkdir(os.path.join(outputdir, 'events'))
    os.mkdir(os.path.join(outputdir, 'pages'))
  
    info('Copying static files')

    shutil.copytree(staticdir, os.path.join(outputdir, 'static'))

    parse_pads()

    info('Read pads')
    info('Generating output')

    produsers = collectionFor('produser')
    events = collectionFor('event')
    pages = collectionFor('page')


    grouped_produsers = sorted(regroup(sorted(produsers.models, key=lambda produser: try_attributes(produser, ['name', 'produser'])), 'role'), key=lambda group: produser_role_sorting.index(group[0]) if group[0] in produser_role_sorting else inf)

    output(os.path.join(outputdir, 'produsers.html'), 'produsers.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers })
    output(os.path.join(outputdir, 'produsers.layout.html'), 'produsers.layout.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers  })

    # for produser in produsers.models:
    #   output(os.path.join(outputdir, produser.prefix, '{}.html'.format(produser.key)), 'produser.html', { 'produser': produser })

    # for event in events.models:
    #   output(os.path.join(outputdir, event.prefix, '{}.html'.format(event.key)), 'event.html', { 'event': event })


    generate_single_pages(produsers, 'produser.html', outputdir, lambda produser: { 'produser': produser })
    generate_single_pages(events, 'event.html', outputdir, lambda event: { 'event': event })
    generate_single_pages(pages, 'page.html', outputdir, lambda page: { 'page': page })

    output(os.path.join(outputdir, 'index.html'), 'index.html', { 'events': sorted(events.models, key=lambda event: try_attributes(event, ['date']), reverse=True) })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
