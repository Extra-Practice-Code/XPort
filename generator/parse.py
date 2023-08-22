import markdown
import os.path

from ethertoff.utils import getPadMarkdown

from generator.models import resolveReferences
from generator.collection import collectionFor, UnknownContentTypeError, knownContentType, knownContentTypes
from generator.utils import error, info, debug, warn, keyFilter

from django.core.management.base import BaseCommand
from django.utils.safestring import mark_safe
from etherpadlite.models import Pad

from .settings import DEFAULT_CONTENT_TYPE

from django.conf import settings

from generator.extract_meta import extract_meta

from bs4 import BeautifulSoup
import copy

def findContextParent (element):
  eligible = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'div']
  parent = element.parent

  if parent:
    if parent.name in eligible:
      return parent
    else:
      return findContextParent(parent)
  else:
    return None

def findLink(link_id, links):
  for link in links:
    if link and link.id == link_id:
      return link

  return None

"""
  Add context parent for inline links.
"""
def addContextForReferences (html, links):
  # try:
  soup = BeautifulSoup(html, 'html.parser')
  references = soup.select('[data-link-id]')
  for reference in references:
    link_id = reference.get('data-link-id')
    
    if link_id:
      link = findLink(link_id, links)

      if link:
        context = copy.copy(findContextParent(reference))
        # Make a copy, remove link elements, keep a span
        # for the marked link
        if context:
          for a in context.select('a'):
            if 'data-link-id' in a and a['data-link-id'] == link_id:
              span = soup.new_tag('span')
              span['data-link-marked'] = 'true'
              span['class'] = 'inline-reference'
              span.string = a.string
              a.replace_with(span)
            else:
              a.unwrap()
              
          link.context = mark_safe(str(context))

"""
  
  Loop through all the pads and 'parse' them as markdown.
  This should return both the content and a dictionary for the metadata

  From this information a model is contstructed. The metadata is further
  parsed depending the field type.

  Links will try to look up their targets. If the target pad isn't parsed yet
  a stub is created to be filled later in the process. 

  TODO: decouple metadata parsing and linking. To make sure all data is seen
  before linking is performed.

  If both keys and labels are used to address models. Depending the order of
  encountering we might create an instance for the label and another for the
  key. Especially when the label / title is later changed.

"""
def parse_pads (prefix=None):
  models = []

  if prefix:
    pads = Pad.objects.filter(display_slug__startswith=prefix)
  else:
    pads = Pad.objects.all()

  for pad in pads:

    name, extension = os.path.splitext(pad.display_slug)
    
    info('Reading {}'.format(pad.display_slug))

    try:
      source = getPadMarkdown(pad).strip()
    except ValueError:
      warn('Could not find pad {}'.format(pad.display_slug))
      continue


    if extension in ['.md', '.markdown']:
      # source, collectedLinkTargets = resolveReferences(source, source=None)

      # md = markdown.Markdown(extensions=['extra', 'meta', TocExtension(baselevel=2), 'attr_list'])
      # content = mark_safe(md.convert(source))
      meta, content = extract_meta(source)
      label = None

      try:
        meta['pk'] = pad.pk
        meta['display_slug'] = pad.display_slug

        # Add the sourcepath as an entry in the metadata?

        # if the first line of the metadata is a known contenttype
        # use it as such. It's value becomes the key and potentially
        # the label
        firstMetaKey, firstMetaValue = list(meta.items())[0]
        
        if knownContentType(firstMetaKey):
          contentType = firstMetaKey
          key = keyFilter(firstMetaValue)
          label = firstMetaValue

          if 'type' in meta:
            warn('Both valid contenttype present in the first row ({0}) as well as a type declaration ({1}), using {0}'.format(contentType, meta['type'][0]), pad.display_slug)
        else:
          if 'type' in meta:
            contentType = meta['type'][0]
          else:
            debug("No contenttype found, applied default contenttype ({}) for: {}".format(DEFAULT_CONTENT_TYPE, pad.display_slug))
            contentType = DEFAULT_CONTENT_TYPE

          key = collectionFor(contentType).model.extractKey(meta)

        
        if key != '':
          debug('Extracted key: {}'.format(key))
          collection = collectionFor(contentType)
          model = collection.instantiate(key=key, label=label, metadata=meta, content=content, source_path=pad.display_slug, source_pad=pad)

          ## @FIXME perhaps move this into the model itself?
          if 'status' in model.fields:
            if model.fields['status'].value == 'published':
              models.append(model)
            else:
              debug("Did not add {} ({}) because it has a status field but it wasn't set to published".format(model.label, model.contentType))
              collection.remove(model)
          else:
            models.append(model)
        else:
          error("Skipped {}, no key".format(pad.display_slug))

      except UnknownContentTypeError as e:
        error(e)
        error('Skipped `{}`, no content type found'.format(name))
        pass

    info('Read {}'.format(pad.display_slug))

  # Excecuting links
  for model in models:
    info('Parsing {} ({})'.format(model.label, model.source_path))
    # resolve links
    debug('Resolving links in the header')
    model.resolveLinks()
    
    if model.content:
      # Render inline references
      debug('Resoving inline references')
      content, links = resolveReferences(model) # Second return are the collected references
      # render markdown
      debug('Parsing markdown')
      md = markdown.Markdown(**settings.MARKDOWN_SETTINGS)
      model.content = mark_safe(md.convert(content))
      # Load context into references?
      if model.content:
        debug('Enriching references with context')
        # As a plugin / optional?
        addContextForReferences(model.content, links)
      
  return models

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'


  def handle(self, *args, **options):
    parse_pads()
