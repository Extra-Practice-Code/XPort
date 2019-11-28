import markdown
import os.path
import urllib

from .models import modelFor, collectionFor, UnknownContentTypeError, knownContentTypes, resolveReferences, knownContentType
from .utils import info, debug, warn, keyFilter

from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient

from django.core.management.base import BaseCommand
from django.utils.safestring import mark_safe
from etherpadlite.models import Pad

from .settings import DEFAULT_CONTENT_TYPE

from django.conf import settings

from generator.extract_meta import extract_meta

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

def parse_pads ():
  epclient = None
  models = []

  for pad in Pad.objects.all():
    if not epclient:
      epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)

    name, extension = os.path.splitext(pad.display_slug)
    padID = pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(settings.PAD_NAMESPACE_SEPARATOR, '_'))
    
    info('Reading {}'.format(pad.display_slug))

    try:
      source = epclient.getText(padID)['text']
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
        # meta = md.Meta
        meta['pk'] = pad.pk

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
            if meta['type'] == ['biography']:
              warn("Outdated contenttype biography. for pad: {}".format(pad.display_slug))
              meta['type'] = ['produser']
            contentType = meta['type'][0]
          else:
            debug("No contenttype found, applied default contenttype for pad: {}".format(pad.display_slug))
            contentType = DEFAULT_CONTENT_TYPE
          key = modelFor(contentType).extractKey(meta)

        collection = collectionFor(contentType)
        
        debug('Extracted key: {}'.format(key))
        model = collection.instantiate(key=key, label=label, metadata=meta, content=content, source_path=pad.display_slug)
        models.append(model)
        # resolveReferences()

        # if collectedLinkTargets:
        #   # print('Collected link targets')
        #   for linkTarget in collectedLinkTargets:
        #     # print(linkTarget.contentType, linkTarget)

        #     # TODO, simplify linking process
        #     # make references to more than just tags
        #     if linkTarget.contentType == 'tag' and 'tags' in model.metadataFields:
        #       current = model.tags if hasattr(model, 'tags') else []

        #       if linkTarget not in current:
        #         model.tags = current + model.metadataFields['tags']([str(linkTarget)], model)

      except UnknownContentTypeError as e:
        debug('Skipped `{}`'.format(name))
        debug(e)
        pass

    info('Read {}'.format(pad.display_slug))

    # Excecuting links
  for model in models:
    # resolve links
    # collect inline links
    model.resolveLinks()
    
    if model.content:
      # Render inline references
      content, _ = resolveReferences(model) # Second return are the collected references
      # render markdown
      md = markdown.Markdown(extensions=['extra', TocExtension(baselevel=2), 'attr_list'])
      model.content = mark_safe(md.convert(content))
      
  return models

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'


  def handle(self, *args, **options):
    parse_pads()

    for produser in collectionFor('produser').models:
      for k in dir(produser):
        info(getattr(produser, k))

    # print(collectionFor('produser').models)
    # print(collectionFor('event').models, collectionFor('event').models[0].metadata, collectionFor('event').models[0].metadata['produser'].metadata)
