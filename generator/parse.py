import markdown
import os.path
import urllib

from .models import modelFor, collectionFor, UnknownContentTypeError, knownContentTypes
from .utils import info, debug, error, warn, keyFilter

from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient

from django.core.management.base import BaseCommand, CommandError
from django.utils.safestring import mark_safe
from etherpadlite.models import Pad

from .settings import DEFAULT_CONTENT_TYPE

from ethertoff.settings import PAD_NAMESPACE_SEPARATOR, BASE_DIR, DEBUG

"""
  
  We loop through all the pads and 'parse' them as markdown.
  This should return both the content and a dictionary for the metadata

  From this information a model is contstructed. The metadata is further
  parsed depending the field type.

  Links will try to look up their targets. If the pad isn't parsed yet a 
  stub is created to be filled later in the process. 

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
    padID = pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(PAD_NAMESPACE_SEPARATOR, '_'))
    source = epclient.getText(padID)['text']

    info('Reading {}'.format(pad.display_slug))

    if extension in ['.md', '.markdown']:
      md = markdown.Markdown(extensions=['extra', 'meta', TocExtension(baselevel=2), 'attr_list'])
      content = mark_safe(md.convert(source))

      try:
        meta = md.Meta
        meta['pk'] = pad.pk

        # if the first line of the metadata is a known contenttype
        # use it as such. It's value becomes the key and potetntially
        # the label
        firstMetaKey, firstMetaValue = list(meta.items())[0]

        if firstMetaKey in knownContentTypes:
          contentType = firstMetaKey
          key = keyFilter(firstMetaValue)

          if 'type' in meta:
            warn('Both valid contenttype present in the first row ({0}) as well as a type declaration ({1}), using {0}'.format(contentType, meta['type'][0]), pad.display_slug)
        else:
          if 'type' in meta:
            if meta['type'] == ['biography']:
              meta['type'] = ['produser']
            contentType = meta['type'][0]
          else:
            contentType = DEFAULT_CONTENT_TYPE
          key = modelFor(contentType).extractKey(meta)

        collection = collectionFor(contentType)
                
        debug('Extracted key: {}'.format(key))
        model = collection.get(key=key)
        models.append(model)

        if model.empty:
          debug('Filling model {}'.format(key))
          model.fill(metadata=meta, content=content, source_path=pad.display_slug)
        else:
          error('Model for key {} already filled'.format(key))

      except UnknownContentTypeError as e:
        debug('Skipped `{}`'.format(name))
        debug(e)
        pass

    info('Read {}'.format(pad.display_slug))
    
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