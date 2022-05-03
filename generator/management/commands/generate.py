# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import re

from generator.index import make_index

from generator.parse import parse_pads
from generator.collection import resetCollections, contentTypes
from generator.utils import debug, info, render_template_to_string, keyFilter
import generator.local_models

from django.core.management.base import BaseCommand
from django.core.management import call_command

from django.conf import settings

FIELD_SINGLE = 'FIELD_SINGLE'
FIELD_ITERABLE = 'FIELD_ITERABLE'

FIELD_DATE_FORMAT = '%d.%m.%Y'
FIELD_DATETIME_FORMAT = '%d-%m-%Y %H:%M'
FIELD_TIME_FORMAT = '%H:%M'


from generator.settings import DATE_OUTPUT_FORMAT

# List pads
# Go through them, record information
# Feed content to templates

def output (path, template, context):
  with open(path, 'w', encoding='utf-8') as w:
    info('Writing {} -> {}'.format(template, path))
    w.write(render_template_to_string(template, context))


def generate_single_pages (models, template, outputdir, make_context):
  for model in models:
    debug('Generating single page for {}'.format(model))
    output(os.path.join(outputdir, '{}.html'.format(keyFilter(model.key))), template, make_context(model))


def generate ():
  # Clear existing collections
  resetCollections(contentTypes)

  basedir = os.path.join(settings.BASE_DIR, 'generator')
  backupdir = os.path.join(basedir, 'static', 'generator', 'generated.old')
  finaldir = os.path.join(basedir, 'static', 'generator', 'generated')
  outputdir = os.path.join(basedir, 'static', 'generator', 'generated.new')

  if os.path.exists(outputdir):
    shutil.rmtree(outputdir)
  
  os.mkdir(outputdir)
    
  info('Parsing pads')
  models = parse_pads()

  info('Read pads')
  info('Generating output')

  
  for contentType in contentTypes.values():
    collection = contentType.collection
    model = collection.model

    if model.generateSinglePages and collection.models:
      singlepagedir = os.path.join(outputdir, model.prefix)
      if not os.path.exists(singlepagedir):
        os.mkdir(singlepagedir)
      debug('Generating single pages for {} in {}'.format(model.contentType, singlepagedir))
      generate_single_pages(collection.models, model.singlePageTemplate, singlepagedir, lambda model: { 'object': model, model.contentType: model, 'page_content': { 'collection': collection, 'content_type': model.contentType, 'model': model } })

    if model.generateListPage:
      output(os.path.join(outputdir, '{}.html'.format(model.plural)), model.listPageTemplate, {
        'page_content': { 'collection': collection, 'content_type': model.contentType },
        'title': model.plural.title(),
        'objects': collection.models
      })

  output(os.path.join(outputdir, 'index.html'), 'generator/index.html', {
    contentType.collection.model.plural: contentType.collection.models for contentType in contentTypes.values()
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
