# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import re

from generator.index import make_index

from generator.parse import parse_pads
from generator.collection import collectionFor, resetCollections, contentTypes
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

"""

    Monkey patching the ThumbnailerMixin to force gif images on dither as the mixin
    prevents to use a custom namer: https://github.com/django-cms/django-filer/issues/1093

"""

from filer.utils.filer_easy_thumbnails import ThumbnailerNameMixin

def patched_get_thumbnail_name(self, thumbnail_options, transparent=False):
    """
    A version of ``Thumbnailer.get_thumbnail_name`` that produces a
    reproducible thumbnail name that can be converted back to the original
    filename.
    """
    path, source_filename = os.path.split(self.name)
    source_extension = os.path.splitext(source_filename)[1][1:].lower()
    preserve_extensions = self.thumbnail_preserve_extensions
    if 'dither' in thumbnail_options:
      # Force gif when dither is activated.
      extension = 'gif'
    elif preserve_extensions is True or source_extension == 'svg' or \
            isinstance(preserve_extensions, (list, tuple)) and source_extension in preserve_extensions:
        extension = source_extension
    elif transparent:
        extension = self.thumbnail_transparency_extension
    else:
        extension = self.thumbnail_extension
    extension = extension or 'jpg'

    thumbnail_options = thumbnail_options.copy()
    size = tuple(thumbnail_options.pop('size'))
    initial_opts = ['{0}x{1}'.format(*size)]
    quality = thumbnail_options.pop('quality', self.thumbnail_quality)
    if extension == 'jpg':
        initial_opts.append('q{}'.format(quality))
    elif extension == 'svg':
        thumbnail_options.pop('subsampling', None)
        thumbnail_options.pop('upscale', None)

    opts = list(thumbnail_options.items())
    opts.sort()   # Sort the options so the file name is consistent.
    opts = ['{}'.format(v is not True and '{}-{}'.format(k, v) or k)
            for k, v in opts if v]
    all_opts = '_'.join(initial_opts + opts)

    basedir = self.thumbnail_basedir
    subdir = self.thumbnail_subdir

    # make sure our magic delimiter is not used in all_opts
    all_opts = all_opts.replace('__', '_')
    filename = '{}__{}.{}'.format(source_filename, all_opts, extension)

    return os.path.join(basedir, path, subdir, filename)


ThumbnailerNameMixin.get_thumbnail_name = patched_get_thumbnail_name




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

    info('Treating: {}'.format(model.contentType))

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
        'objects': collection.models,
        'collection': collection
      })

  galleryImagesPage = collectionFor('snippet').get('gallery-images')

  output(os.path.join(outputdir, 'gallery.html'), 'generator/list--galleries.html', {
    'galleries': collectionFor('gallery').models,
    'videos': collectionFor('video').models,
    'galleryImagesPage': galleryImagesPage,
    'page_content': { 'content_type': 'gallery' }
  })


  output(os.path.join(outputdir, 'reflections.html'), 'generator/reflections.html', {
    'contributions': collectionFor('contribution').models,
    'reflections': collectionFor('reflection').models,
    'previewreviews': collectionFor('previewreview').models,
    'sharedspaces': collectionFor('sharedspace').models,
    'page_content': { 'content_type': 'reflection' }
  })


  output(os.path.join(outputdir, 'index.html'), 'generator/index.html', { 
    'home': collectionFor('snippet').get('home'),
    'homeItems': collectionFor('snippet').get('home-items')
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
