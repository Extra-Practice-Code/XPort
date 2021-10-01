# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import re

from math import inf
from generator.index import make_index

from generator.parse import parse_pads
from generator.models import collectionFor, resetCollections, contentTypes
from generator.utils import info, regroup, try_attributes, render_to_string, keyFilter

from django.core.management.base import BaseCommand
from django.core.management import call_command

from django.conf import settings

from generator.templatetags.generator_utils import link_iterator, link_target_iterator

FIELD_SINGLE = 'FIELD_SINGLE'
FIELD_ITERABLE = 'FIELD_ITERABLE'

FIELD_DATE_FORMAT = '%d.%m.%Y'
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
    output(os.path.join(outputdir, model.prefix, '{}.html'.format(keyFilter(model.key))), template, make_context(model))

def datesorter (obj):
  if hasattr(obj, 'date'):
    date = getattr(obj, 'date').value

    if isinstance(date, Date):
      return date.date
    elif isinstance(date, DateRange):
      return date.start.date
    
  return datetime.date(1,1,1)

def timesorter (obj):
  if hasattr(obj, 'time'):
    time = getattr(obj, 'time').value

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
  # print(list(link_target_iterator(event.programmeItems)))
  programmeItems = sorted(event.programmeItems.targets, key=datetimesorter)
  return regroup(programmeItems, lambda e: datesorter(e).strftime(DATE_OUTPUT_FORMAT))

def generate ():
  # Clear existing collections
  resetCollections(contentTypes)
  basedir = os.path.join(settings.BASE_DIR, 'generator')
  # staticdir = os.path.join(basedir, 'templates', 'static')
  backupdir = os.path.join(basedir, 'static', 'generator', 'generated.old')
  finaldir = os.path.join(basedir, 'static', 'generator', 'generated')
  outputdir = os.path.join(basedir, 'static', 'generator', 'generated.new')

  if os.path.exists(outputdir):
    shutil.rmtree(outputdir)
  
  os.mkdir(outputdir)
  
  # print('Copying static files')
  # shutil.copytree(staticdir, os.path.join(outputdir, 'static'))

  print('Parsing pads')
  os.mkdir(os.path.join(outputdir, 'conversations'))
  os.mkdir(os.path.join(outputdir, 'demonstrations'))
  os.mkdir(os.path.join(outputdir, 'protocols'))
  os.mkdir(os.path.join(outputdir, 'themes'))
  os.mkdir(os.path.join(outputdir, 'elements'))
  os.mkdir(os.path.join(outputdir, 'locations'))
  os.mkdir(os.path.join(outputdir, 'tools'))
  os.mkdir(os.path.join(outputdir, 'shores'))
  os.mkdir(os.path.join(outputdir, 'images'))
  os.mkdir(os.path.join(outputdir, 'audio'))
  
  models = parse_pads()

  print('Read pads')
  print('Generating output')

  protocols = collectionFor('protocol')
  demonstrations = collectionFor('demonstration')
  conversations = collectionFor('conversation')
  themes = collectionFor('theme')
  elements = collectionFor('element')
  locations = collectionFor('location')
  tools = collectionFor('tool')
  shores = collectionFor('shore')
  images = collectionFor('image')
  audios = collectionFor('audio')
  
  # events = collectionFor('event')
  # pages = collectionFor('page')
  # tags = collectionFor('tag')
  # bibliography = collectionFor('bibliography')
  # externalProjects = collectionFor('external-project')
  # notes = collectionFor('notes')
  # trajectories = collectionFor('trajectory')
  # questions = collectionFor('question')
  # reflections = collectionFor('reflection')

  # def getProduserSortKey (produser):
  #   attr = try_attributes(produser, ['sortname', 'name', 'produser'])

  #   if attr and attr.value:
  #     return attr.value.lower()
  #   else:
  #     return None

  # def getTrajectorySortKey (trajectory):
  #   if trajectory.produser.resolved:
  #     return getProduserSortKey(trajectory.produser.target)
  #   else:
  #     return ''

  def getLabelAsSortKey (model):
    label = getattr(model, model.labelField)

    if label and label.value:
      return label.value.lower()
    else:
      return ''

  # def makeGroupSorter (order):
  #   def sorter (line):
  #     sortKey = line[0]
  #     return order.index(sortKey) if sortKey in order else inf

  #   return sorter

  def makeAttributeSorter(attributes):
    def sorter (model):
      return str(try_attributes(model, attributes)).lower()

  def sortedByLabel(models):
    return sorted(models, key=getLabelAsSortKey)

  #   return sorter

  # ## Produsers
  # ## First 
  # produser_role_sorting = ['artist', 'co-producer', 'other professional', 'team', 'partner']
  # sorted_produsers = sorted(produsers.models, key=getProduserSortKey)
  # grouped_produsers = sorted(regroup(sorted_produsers, 'role'), key=makeGroupSorter(produser_role_sorting))

  # output(
  #   os.path.join(outputdir, 'produsers.html'), 
  #   'produsers.html', 
  #   { 
  #     'produsers': sorted(produsers.models, key=makeAttributeSorter(['sortname', 'name', 'produser', 'key'])), 
  #     'grouped_produsers': grouped_produsers })
  
  # # output(os.path.join(outputdir, 'produsers.layout.html'), 'produsers.layout.html', { 'produsers': sorted(produsers.models, key=lambda r: str(r.key)), 'grouped_produsers': grouped_produsers  })
  
  # ## Tags
  # sorted_tags = sorted(tags.models, key=lambda m: re.subn(r'\W', '', str(m))[0].lower())
  # grouped_tags = regroup(sorted_tags, key=lambda m: re.subn(r'\W', '', str(m))[0].lower()[0])
  # output(
  #   os.path.join(outputdir, 'tags.html'), 
  #   'tags.html', 
  #   { 'tags': sorted_tags, 'grouped_tags': grouped_tags })
  
  # ## Bibliography
  # output(
  #   os.path.join(outputdir, 'bibliography.html'),
  #   'bibliography.html', 
  #   { 'bibliography': sorted(bibliography.models, key=getLabelAsSortKey) })
  
  # ## External projects
  # output(
  #   os.path.join(outputdir, 'external-projects.html'),
  #   'external-projects.html',
  #   { 'externalProjects': sorted(externalProjects.models, key=getLabelAsSortKey) })
  
  # ## Trajectories
  # trajectory_category_sorting = ['artisttrajectory', 'designertrajectory', 'reflection']
  # sorted_trajectories = sorted(trajectories.models, key=getTrajectorySortKey)
  # grouped_trajectories = sorted(regroup(sorted_trajectories, 'category'), key=makeGroupSorter(trajectory_category_sorting))
  # output(
  #   os.path.join(outputdir, 'trajectories.html'),
  #   'trajectories.html', 
  #   {
  #     'trajectories': sorted_trajectories,
  #     'grouped_trajectories': grouped_trajectories,
  #     'reflections': sorted(reflections.models, key=getLabelAsSortKey)
  #   })

  # # for trajectory in trajectories.models:
  # #   if trajectory.title.value:
  # #     output(os.path.join(outputdir, trajectory.prefix, '{}.html'.format(keyFilter(trajectory.title))), 'trajectory.html', { 'trajectory': trajectory })

  # ## Questions
  # output(
  #   os.path.join(outputdir, 'questions.html'),
  #   'questions.html',
  #   { 'questions': questions.models }
  # )

  # # for produser in produsers.models:
  # #   output(os.path.join(outputdir, produser.prefix, '{}.html'.format(produser.key)), 'produser.html', { 'produser': produser })

  # # for event in events.models:
  # #   output(os.path.join(outputdir, event.prefix, '{}.html'.format(event.key)), 'event.html', { 'event': event })


  generate_single_pages(conversations.models, 'generator/conversation.html', outputdir, lambda conversation: { 'conversation': conversation })
  generate_single_pages(demonstrations.models, 'generator/demonstration.html', outputdir, lambda demonstration: { 'demonstration': demonstration })
  generate_single_pages(protocols.models, 'generator/protocol.html', outputdir, lambda protocol: { 'protocol': protocol })

  generate_single_pages(locations.models, 'generator/object.html', outputdir, lambda location: { 'object': location })
  generate_single_pages(elements.models, 'generator/object.html', outputdir, lambda element: { 'object': element })
  generate_single_pages(themes.models, 'generator/object.html', outputdir, lambda theme: { 'object': theme })
  generate_single_pages(tools.models, 'generator/object.html', outputdir, lambda tool: { 'object': tool })
  generate_single_pages(shores.models, 'generator/object.html', outputdir, lambda shore: { 'object': shore })
  generate_single_pages(images.models, 'generator/object.html', outputdir, lambda image: { 'object': image })
  generate_single_pages(audios.models, 'generator/object.html', outputdir, lambda audio: { 'object': audio })

  # output(os.path.join(outputdir, 'activities.html'), 'activities.html', { 'events': sorted(events.models, key=datesorter, reverse=True) })
  
  # output(os.path.join(outputdir, 'index.old.html'), 'index.html', { 'events': sorted(events.models, key=datesorter, reverse=True) })
  output(os.path.join(outputdir, 'index.html'), 'generator/index.html', { 
    'protocols': protocols.models,
    'demonstrations': demonstrations.models,
    'conversations': conversations.models,
    'themes':  sortedByLabel(themes.models),
    'elements': sortedByLabel(elements.models),
    'locations': sortedByLabel(locations.models),
    'tools': sortedByLabel(tools.models),
    'shores': sortedByLabel(shores.models),
    'images': images.models,
    'audios': audios.models
   })

  with open(os.path.join(outputdir, 'debug.html'), 'w', encoding='utf-8') as w:
    w.write(make_index(models))


  info('Making backup of previous version, putting new version in place')

  if os.path.exists(outputdir):
    # Test whether there is an existing version of the site
    if os.path.exists(finaldir):
      # Removing old backup if it exists
      if os.path.exists(backupdir):
        shutil.rmtree(backupdir)
      
      # Put new backup in place
      shutil.move(finaldir, backupdir)
    
    # Put new version of the site in place
    shutil.move(outputdir, finaldir)

  if not settings.DEBUG:
    print('Collecting static')
    call_command('collectstatic', interactive=False)

  print('Done')

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    generate()
