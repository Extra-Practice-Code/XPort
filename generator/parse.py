import markdown
import os.path
import urllib

from .models import modelFor, collectionFor, UnknownContentTypeError
from .utils import info, debug, error

from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient

from django.core.management.base import BaseCommand, CommandError
from django.utils.safestring import mark_safe
from etherpadlite.models import Pad

from ethertoff.settings import PAD_NAMESPACE_SEPARATOR, BASE_DIR, DEBUG

def parse_pads ():
  epclient = None
  
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

        if 'type' not in meta:
          meta['type'] = ['pad']

        if meta['type'] == ['biography']:
          meta['type'] = ['produser']


        collection = collectionFor(meta['type'][0])
        
        key = modelFor(meta['type'][0]).extractKey(meta)
        debug('Extracted key: {}'.format(key))
        model = collection.get(key)
        if model.empty:
          debug('Filling model {}'.format(key))
          model.fill(metadata=meta, content=content)
        else:
          error('Model for key {} already filled'.format(key))

      except UnknownContentTypeError as e:
        print('Skipped `{}`'.format(name))
        print(e)
        pass

    info('Read {}'.format(pad.display_slug))

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'


  def handle(self, *args, **options):
    parse_pads()

    for produser in collectionFor('produser').models:
      for k in dir(produser):
        print(getattr(produser, k))

    # print(collectionFor('produser').models)
    # print(collectionFor('event').models, collectionFor('event').models[0].metadata, collectionFor('event').models[0].metadata['produser'].metadata)