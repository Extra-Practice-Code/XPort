# -*- coding: utf-8 -*-

import os
import os.path
import shutil

# Do not remove, registers the local models!
import generator.local_models

from generator.settings import SITE_URL, MENU_ITEMS, STATIC_URL
from generator.index import make_index
from generator.parse import parse_pads
from generator.collection import collectionFor, resetCollections, contentTypes, setCollectionsContext
from generator.utils import debug, info, render_template_to_string, keyFilter

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

from ethertoff.utils import discover_root_folders, pathToSlugPrefix, discover_pad, copyPadToPath
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

def extend_context (context, new_properties):
  context.update(new_properties)
  return context

def generate ():

  root_folders = discover_root_folders()

  info('Discovered {} root folders: {}'.format(len(root_folders), ', '.join(root_folders)))

  for folder in root_folders:
    context = {
      'SITE_URL': SITE_URL.format(PUBLICATION_NAME=folder),
      'STATIC_URL': STATIC_URL.format(PUBLICATION_NAME=folder),
      'MENU_ITEMS': MENU_ITEMS
    }  

    print(context)

    info('Generating {}'.format(folder))

    # Clear existing collections
    resetCollections()
    setCollectionsContext(context)

    basedir = os.path.join(settings.BASE_DIR, 'generator', 'static', 'generator')
    backupdir = os.path.join(basedir, 'generated.old', folder)
    finaldir = os.path.join(basedir, 'generated', folder)
    outputdir = os.path.join(basedir, 'generated.new', folder)

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.makedirs(outputdir)
      
    info('Parsing pads')
    models = parse_pads(prefix=pathToSlugPrefix([ folder ]))

    info('Read pads')
    info('Generating output')

    for contentType in contentTypes.values():
      collection = contentType.collection
      model = collection.model

      info('Treating: {}'.format(model.contentType))

      if model.generateSinglePages and collection.models:
        singlepagedir = os.path.join(outputdir, model.prefix)
        if not os.path.exists(singlepagedir):
          os.makedirs(singlepagedir)
        debug('Generating single pages for {} in {}'.format(model.contentType, singlepagedir))
        generate_single_pages(collection.models, model.singlePageTemplate, singlepagedir, lambda model: extend_context(context, { 'object': model, model.contentType: model, 'page_content': { 'collection': collection, 'content_type': model.contentType, 'model': model } }))

      if model.generateListPage:
        output(os.path.join(outputdir, '{}.html'.format(model.plural)), model.listPageTemplate, extend_context(context, {
          'page_content': { 'collection': collection, 'content_type': model.contentType },
          'title': model.plural.title(),
          'objects': collection.models,
          'collection': collection
        }))

    output(os.path.join(outputdir, 'index.html'), 'generator/index.html', extend_context(context, {
      'tags': collectionFor('tag'),
      'reports': collectionFor('report')
    }))

    output(os.path.join(outputdir, 'print.html'), 'generator/print.html', extend_context(context, {
      'tags': collectionFor('tag'),
      'reports': collectionFor('report')
    }))

    with open(os.path.join(outputdir, 'debug.html'), 'w', encoding='utf-8') as w:
      w.write(make_index(models))


    css_generated = discover_pad('generated.css', path=[ folder ])
    if css_generated:
      copyPadToPath(css_generated, os.path.join(outputdir, 'generated.css'))
    
    css_print = discover_pad('print.css', path=[ folder ])
    if css_print:
      copyPadToPath(css_print, os.path.join(outputdir, 'print.css'))

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
