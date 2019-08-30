# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil

from math import inf
from generator.index import make_index

import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient
from generator.parse import parse_pads
from generator.models import collectionFor
from generator.utils import info, regroup, try_attributes, render_to_string

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

from generator.fields import Date, DateRange, Time, TimeRange

from generator.settings import DATE_OUTPUT_FORMAT

# List pads
# Go through them, record information
# Feed content to templates

def output (path, template, context):  
  with open(path, 'w', encoding='utf-8') as w:
    info('Writing {} -> {}'.format(template, path))
    w.write(render_to_string(template, context))


def generate_single_pages (models, template, outputdir, make_context):
  for model in models:
    output(os.path.join(outputdir, model.prefix, '{}.html'.format(model.key)), template, make_context(model))

def datesorter (obj):
  if hasattr(obj, 'date'):
    date = getattr(obj, 'date')

    if isinstance(date, Date):
      return date.date
    elif isinstance(date, DateRange):
      return date.start.date
    
  return datetime.date(1,1,1)

def timesorter (obj):
  if hasattr(obj, 'time'):
    time = getattr(obj, 'time')

    if isinstance(time, Time):
      return time.time
    elif isinstance(time, TimeRange):
      return time.start
  
  return datetime.time(0,0)

def datetimesorter (obj):
  date = datesorter(obj)
  time = timesorter(obj)

  return datetime.datetime.combine(date, time)
  
def groupedProgrammeItems(event):
  programmeItems = sorted(event.programmeItems, key=datetimesorter)
  return regroup(programmeItems, lambda e: datesorter(e).strftime(DATE_OUTPUT_FORMAT))

produser_role_sorting = ['artist', 'co-producer', 'other professional', 'team', 'partner']

def generate ():
  basedir = os.path.join(BASE_DIR, 'generator')
  staticdir = os.path.join(basedir, 'templates', 'static')
  outputdir = os.path.join(basedir, 'static', 'generated')

  if os.path.exists(outputdir):
    shutil.rmtree(outputdir)
  
  os.mkdir(outputdir)
  
  print('Copying static files')
  shutil.copytree(staticdir, os.path.join(outputdir, 'static'))

  print('Parsing pads')
  os.mkdir(os.path.join(outputdir, 'produsers'))
  os.mkdir(os.path.join(outputdir, 'activities'))
  os.mkdir(os.path.join(outputdir, 'pages'))
  os.mkdir(os.path.join(outputdir, 'tags'))
  os.mkdir(os.path.join(outputdir, 'notes'))
  
  models = parse_pads()

  print('Read pads')
  print('Generating output')

  produsers = collectionFor('produser')
  events = collectionFor('event')
  pages = collectionFor('page')
  tags = collectionFor('tag')
  bibliography = collectionFor('bibliography')
  externalProjects = collectionFor('external-project')
  notes = collectionFor('notes')
  trajectories = collectionFor('trajectory')

  grouped_produsers = sorted(regroup(sorted(produsers.models, key=lambda produser: try_attributes(produser, ['sortname', 'name', 'produser']).lower()), 'role'), key=lambda group: produser_role_sorting.index(group[0]) if group[0] in produser_role_sorting else inf)

  output(os.path.join(outputdir, 'produsers.html'), 'produsers.html', { 'produsers': sorted(produsers.models, key=lambda r: str(try_attributes(r, ['sortname', 'name', 'produser', 'key'])).lower()), 'grouped_produsers': grouped_produsers })
  # output(os.path.join(outputdir, 'produsers.layout.html'), 'produsers.layout.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers  })
  output(os.path.join(outputdir, 'tags.html'), 'tags.html', { 'tags': sorted(tags.models, key=lambda m: getattr(m, m.labelField)) })
  output(os.path.join(outputdir, 'bibliography.html'), 'bibliography.html', { 'bibliography': sorted(bibliography.models, key=lambda m: getattr(m, m.labelField)) })
  output(os.path.join(outputdir, 'external-projects.html'), 'external-projects.html', { 'externalProjects': sorted(externalProjects.models, key=lambda m: getattr(m, m.labelField)) })
  output(os.path.join(outputdir, 'trajectories.html'), 'trajectories.html', { 'trajectories': trajectories.models })

  # for produser in produsers.models:
  #   output(os.path.join(outputdir, produser.prefix, '{}.html'.format(produser.key)), 'produser.html', { 'produser': produser })

  # for event in events.models:
  #   output(os.path.join(outputdir, event.prefix, '{}.html'.format(event.key)), 'event.html', { 'event': event })


  generate_single_pages(produsers.models, 'produser.html', outputdir, lambda produser: { 'produser': produser })
  generate_single_pages(pages.models, 'page.html', outputdir, lambda page: { 'page': page })
  generate_single_pages(tags.models, 'tag.html', outputdir, lambda tag: { 'tag': tag })
  generate_single_pages(filter(lambda e: not hasattr(e, 'programmeItems') or not e.programmeItems, events.models), 'event.html', outputdir, lambda event: { 'event': event })


  generate_single_pages(filter(lambda e: hasattr(e, 'programmeItems') and e.programmeItems, events.models), 'event-with-programme-items.html', outputdir, lambda event: { 'event': event, 'groupedProgrammeItems': groupedProgrammeItems(event)})
  generate_single_pages(notes.models, 'note.html', outputdir, lambda note: { 'note': note })
  

  output(os.path.join(outputdir, 'activities.html'), 'activities.html', { 'events': sorted(events.models, key=datesorter, reverse=True) })
  
  output(os.path.join(outputdir, 'index.html'), 'index.html', { 'events': sorted(events.models, key=datesorter, reverse=True) })

  with open(os.path.join(outputdir, 'debug.html'), 'w', encoding='utf-8') as w:
    w.write(make_index(models))

  if not DEBUG:
    print('Collecting static')
    call_command('collectstatic', interactive=False)

  print('Done')

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    generate()
