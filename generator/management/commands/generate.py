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
from django.contrib.staticfiles import finders

from ethertoff.utils import pathToSlugPrefix, discoverPad, copyPadToPath, stripLeadingAsterisks, getPadBySlug, pathToSlug, getPadText
from labels.utils import load_labels

from ethertoff.models import EtherportOrganisation

FIELD_SINGLE = 'FIELD_SINGLE'
FIELD_ITERABLE = 'FIELD_ITERABLE'

FIELD_DATE_FORMAT = '%d.%m.%Y'
FIELD_DATETIME_FORMAT = '%d-%m-%Y %H:%M'
FIELD_TIME_FORMAT = '%H:%M'

# Fix urls of css stylesheets make them relative for archiving purposes

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

def get_publication_labels (labels, organisation_slug, folder):
  if organisation_slug in labels:
    if folder in labels[organisation_slug]:
      return labels[organisation_slug][folder]
    elif 'root' in labels[organisation_slug]:
      return labels[organisation_slug]['root']
    
  return []

"""
  Generate static versions of publications
  folders: None,list<foldername>,dict<foldername: mode>
  
"""
def generate (organisation_slug, folders=None):
  labels = load_labels()

  # List of publications: [{ title: str, path: str, url: str }, ...]
  publications = []

  if not folders:
      folders = { folder: 'normal' for folder in discoverPublicationFolders(organisation_slug) }
  elif type(folders) is list:
      folders = { folder: 'normal' for folder in folders }

  basedir = os.path.join(settings.BASE_DIR, 'generator', 'static', 'generator')

  for folder, mode in folders.items():
    info('Generating {}'.format(folder))

    # Clear existing collections
    resetCollections()

    backupdir = os.path.join(basedir, 'generated.old', organisation_slug, folder)
    finaldir = os.path.join(basedir, 'generated', organisation_slug, folder)
    outputdir = os.path.join(basedir, 'generated.new', organisation_slug, folder)

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.makedirs(outputdir)
      
    info('Parsing pads')
    models = read_pads(prefix=pathToSlugPrefix([ organisation_slug, folder ]))

    info('Read pads')
    index_pad = find_where(collectionFor('pad'), {'index': 'true'})
    
    footer_pad = getPadBySlug(pathToSlug([organisation_slug, folder, 'template-snippets', 'footer.html']))

  

    context = {
      'SITE_URL': SITE_URL.format(ORGANISATION_SLUG=organisation_slug, PUBLICATION_NAME=folder) if not index_pad or not index_pad.metadata['site-url'].value else index_pad.metadata['site-url'].value,
      'STATIC_URL': STATIC_URL.format(ORGANISATION_SLUG=organisation_slug, PUBLICATION_NAME=folder) if not index_pad or not index_pad.metadata['static-url'].value else index_pad.metadata['static-url'].value,
      'MENU_ITEMS': MENU_ITEMS,
      'LABELS': get_publication_labels(labels, organisation_slug, folder),
      'SNIPPETS': {
        'FOOTER': getPadText(footer_pad) if footer_pad else None
      }
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
      context['PATH_CSS_GENERATED'] = ETHERTOFF_URL + reverse('css-generator-screen', kwargs={ 'organisation_slug': organisation_slug, 'folder': folder })
      context['PATH_CSS_PRINT'] = ETHERTOFF_URL + reverse('css-generator-print', kwargs={ 'organisation_slug': organisation_slug, 'folder': folder })
                                                          
      file_js = discoverPad('scripts.js', path=[ organisation_slug, folder ])
      if file_js:                                     
        context['PATH_JAVASCRIPT'] = ETHERTOFF_URL + reverse('javascript-generator', kwargs={ 'organisation_slug': organisation_slug, 'folder': folder })
      else:
        context['PATH_JAVASCRIPT'] = None

      file_print_js = discoverPad('scripts-print.js', path=[ organisation_slug, folder ])
      if file_print_js:
        context['PATH_JAVASCRIPT_PRINT'] = ETHERTOFF_URL + reverse('javascript-generator-print', kwargs={ 'organisation_slug': organisation_slug, 'folder': folder })
      else:
        context['PATH_JAVASCRIPT_PRINT'] = None
    else:
      file_css_generated = discoverPad('generated.css', path=[ organisation_slug, folder ])
      if file_css_generated:
        debug("Copying pad '{}' to '{}'".format(file_css_generated, os.path.join(outputdir, 'generated.css')))
        copyPadToPath(file_css_generated, os.path.join(outputdir, 'generated.css'), stripLeadingAsterisks)
        context['PATH_CSS_GENERATED'] = context['SITE_URL'] + '/generated.css'
      else:
        context['PATH_CSS_GENERATED'] = None
        warn("Could not find a generated.css")
      
      file_css_print = discoverPad('print.css', path=[ organisation_slug, folder ])
      if file_css_print:
        debug("Copying pad '{}' to '{}'".format(file_css_print, os.path.join(outputdir, 'print.css')))
        copyPadToPath(file_css_print, os.path.join(outputdir, 'print.css'), stripLeadingAsterisks)
        context['PATH_CSS_PRINT'] = context['SITE_URL'] + '/print.css'
      else:
        context['PATH_CSS_PRINT'] = None
        warn("Could not find a print.css")

      file_js = discoverPad('scripts.js', path=[ organisation_slug, folder ])
      if file_js:
        debug("Copying pad '{}' to '{}'".format(file_js, os.path.join(outputdir, 'scripts.js')))
        copyPadToPath(file_js, os.path.join(outputdir, 'scripts.js'), stripLeadingAsterisks)
        context['PATH_JAVASCRIPT'] = context['SITE_URL'] + '/scripts.js'
      else:
        context['PATH_JAVASCRIPT'] = None
        debug("Could not find a scripts.js")

      file_print_js = discoverPad('scripts-print.js', path=[ organisation_slug, folder ])
      if file_print_js:
        debug("Copying pad '{}' to '{}'".format(file_print_js, os.path.join(outputdir, 'scripts-print.js')))
        copyPadToPath(file_print_js, os.path.join(outputdir, 'scripts-print.js'), stripLeadingAsterisks)
        context['PATH_JAVASCRIPT_PRINT'] = context['SITE_URL'] + '/scripts-print.js'
      else:
        context['PATH_JAVASCRIPT_PRINT'] = None
        debug("Did not find a scripts-print.js")


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

    import shutil
    PATH_CSS_PAGEDJS = context['SITE_URL'] + '/pagedjs-interface.css'
    local_path = finders.find('generator/css/interface.css')
    shutil.copy(local_path, os.path.join(outputdir, 'pagedjs-interface.css'))

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
      'chapters': collectionFor('chapter'),
      'PATH_CSS_PAGEDJS': PATH_CSS_PAGEDJS
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


  if not os.path.exists(os.path.join(basedir, 'generated', organisation_slug)):
    os.makedirs(os.path.join(basedir, 'generated', organisation_slug))

  css_publication_list = discoverPad('publication-list.css', path=[ organisation_slug ])
  if css_publication_list:
    debug("Copying pad '{}' to '{}'".format(css_publication_list, os.path.join(basedir, 'generated', 'publication-list.css')))
    copyPadToPath(css_publication_list, os.path.join(basedir, 'generated', organisation_slug, 'publication-list.css'), stripLeadingAsterisks)

  organisation = EtherportOrganisation.objects.get(slug=organisation_slug)

  output(os.path.join(basedir, 'generated', organisation_slug, 'index.html'), 'generator/main_index.html', { 'SITE_URL': GENERATED_SITE_INDEX, 'organisation': organisation, 'publications': publications, 'ETHERTOFF_URL': ETHERTOFF_URL })

  storePublications(organisation_slug, publications)

  organisations = EtherportOrganisation.objects.all()
  output(os.path.join(basedir, 'generated', 'index.html'), 'generator/etherport_index.html', { 'organisations': organisations })


  if not settings.DEBUG:
    info('Collecting static')
    call_command('collectstatic', interactive=False)

  info('Done')


class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    organisations = EtherportOrganisation.objects.all()

    for organisation in organisations:
      info(organisation.name)
      generate(organisation.slug)
