# -*- coding: utf-8 -*-

import os
import os.path
import shutil

# Do not remove, registers the local models!
import generator.local_models

from generator.settings import ETHERTOFF_URL, SITE_URL, MENU_ITEMS, STATIC_URL, GENERATED_SITE_INDEX
from generator.fields import Single
from generator.index import make_index
from generator.parse import read_pads, resolve_links
from generator.collection import collectionFor, resetCollections, contentTypes, setCollectionsContext
from generator.utils import debug, info, render_template_to_string, keyFilter, warn, storePublications, discoverPublicationFolders

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.urls import reverse

from ethertoff.utils import pathToSlugPrefix, discoverPad, copyPadToPath, stripLeadingAsterisks
from labels.utils import load_labels

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

def find_where (collection, attrs):
  for obj in collection.models:
    for attr, value in attrs.items():
      if not hasattr(obj, attr):
        continue

      field = getattr(obj, attr)

      if isinstance(field, Single):
        if field.value != value:
          continue
      else:
        if value not in field.value:
          continue

      return obj

  return None

"""
  Generate static versions of publications
  folders: None,list<foldername>,dict<foldername: mode>
  
"""
def generate (folders=None):
  labels = load_labels()

  # List of publications: [{ title: str, path: str, url: str }, ...]
  publications = []

  if not folders:
      folders = { folder: 'normal' for folder in discoverPublicationFolders() }
  elif type(folders) is list:
      folders = { folder: 'normal' for folder in folders }

  basedir = os.path.join(settings.BASE_DIR, 'generator', 'static', 'generator')

  for folder, mode in folders.items():
    info('Generating {}'.format(folder))

    # Clear existing collections
    resetCollections()

    backupdir = os.path.join(basedir, 'generated.old', folder)
    finaldir = os.path.join(basedir, 'generated', folder)
    outputdir = os.path.join(basedir, 'generated.new', folder)

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.makedirs(outputdir)
      
    info('Parsing pads')
    models = read_pads(prefix=pathToSlugPrefix([ folder ]))

    info('Read pads')
    index_pad = find_where(collectionFor('pad'), {'index': 'true'})

    context = {
      'SITE_URL': SITE_URL.format(PUBLICATION_NAME=folder),
      'STATIC_URL': STATIC_URL.format(PUBLICATION_NAME=folder),
      'MENU_ITEMS': MENU_ITEMS,
      'LABELS': labels[folder] if folder in labels else labels['root']
    }  

    if index_pad:
      info('Found {} as index'.format(index_pad))
      context['PUBLICATION_TITLE'] = str(index_pad.title)
    else:
      info('Did not find and index.')
      context['PUBLICATION_TITLE'] = folder

    publications.append({
      'title': context['PUBLICATION_TITLE'],
      'path': folder,
      'url': context['SITE_URL']
    })

    info('Generating output')

    if mode == 'development':
      css_generated = reverse('css-generator-screen', kwargs={ 'folder': folder })
      css_print = reverse('css-generator-print', kwargs={ 'folder': folder })
  
      print('ethertoff url:', ETHERTOFF_URL)

      context['CSS_GENERATED'] = ETHERTOFF_URL + css_generated
      context['CSS_PRINT'] = ETHERTOFF_URL + css_print
    else:
      css_generated = discoverPad('generated.css', path=[ folder ])
      if css_generated:
        debug("Copying pad '{}' to '{}'".format(css_generated, os.path.join(outputdir, 'generated.css')))
        copyPadToPath(css_generated, os.path.join(outputdir, 'generated.css'), stripLeadingAsterisks)
      else:
        warn("Could not find a generated.css")
      
      css_print = discoverPad('print.css', path=[ folder ])
      if css_print:
        debug("Copying pad '{}' to '{}'".format(css_print, os.path.join(outputdir, 'print.css')))
        copyPadToPath(css_print, os.path.join(outputdir, 'print.css'), stripLeadingAsterisks)
      else:
        warn("Could not find a print.css")

      context['CSS_GENERATED'] = 'generated.css'
      context['CSS_PRINT'] = 'print.css'

    setCollectionsContext(context)

    models = resolve_links(models)

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
      'labels': collectionFor('label'),
      'reports': collectionFor('report'),
      'index_pad': index_pad
    }))

    output(os.path.join(outputdir, 'print.html'), 'generator/print.html', extend_context(context, {
      'index_pad': index_pad,
      'labels': collectionFor('label'),
      'reports': collectionFor('report'),
      'pads': collectionFor('pad'),
      'chapters': collectionFor('chapter')
    }))

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

  css_publication_list = discoverPad('publication-list.css', path=[])
  if css_publication_list:
    debug("Copying pad '{}' to '{}'".format(css_publication_list, os.path.join(basedir, 'generated', 'publication-list.css')))
    copyPadToPath(css_publication_list, os.path.join(basedir, 'generated', 'publication-list.css'), stripLeadingAsterisks)

  output(os.path.join(basedir, 'generated', 'index.html'), 'generator/main_index.html', { SITE_URL: GENERATED_SITE_INDEX, 'publications': publications })

  storePublications(publications)

  if not settings.DEBUG:
    print('Collecting static')
    call_command('collectstatic', interactive=False)

  print('Done')


class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    generate(discoverPublicationFolders())
