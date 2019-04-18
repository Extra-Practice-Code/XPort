# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil


import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient

from django.template import loader
from django.utils.safestring import mark_safe
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from etherpadlite.models import Pad

from ethertoff.settings import PAD_NAMESPACE_SEPARATOR, BASE_DIR, DEBUG

FIELD_SINGLE = 'FIELD_SINGLE'
FIELD_ITERABLE = 'FIELD_ITERABLE'

# List pads
# Go through them, record information
# Feed content to templates


def output (path, template, context):
  with open(path, 'w', encoding='utf-8') as w:
    w.write(loader.render_to_string(template, context))

class Parser(object):
  def __init__ (self):
    self.fields = {
      'produser': {
        'role': FIELD_SINGLE,
        'biography': FIELD_SINGLE,
        'event': FIELD_ITERABLE
      }
    }

    self.linkTargets = ['produser', 'event']
    
    self.contentTypes = ['biography', 'bibliography', 'event', 'meeting', 'notes', 'role']

    self.data = { target: [] for target in self.linkTargets }
    self.index = { target: {} for target in self.linkTargets }

  def findTarget (self, targetName, key):
    if targetName in self.data:
      if key in self.index[targetName]:
        return self.index[targetName][key]
      else:
        target = { '__type__': targetName, 'key': key }
        self.data[targetName].append(target)
        self.index[targetName][key] = target
        
    return target
  def makeContentFragment (self, contentType, value):
    ## Could be more intricate later on
    return { 'type': contentType, 'value': value }

  def setProperty(self, obj, prop, val):
    # If there is a description for the property
    # follow the description: single or plural
    # to extend: overwrite / datafilter
    if obj['__type__'] in self.fields:
      desc = self.fields[obj['__type__']]
      if prop in desc:
        if desc[prop] == FIELD_SINGLE:
          obj[prop] = val
        else:
          if prop not in obj:
            obj[prop] = []

          obj[prop].append(val)

    else:
      if prop not in obj:
        obj[prop] = []

      obj[prop].append(val)

  # Rename function
  def makeLinks(self, meta, contentFragment):
    for targetName in self.linkTargets:
      if targetName in meta:
        for target in meta[targetName]:
          targetObj = self.findTarget(targetName, target.strip(' ;'))
          self.setProperty(targetObj, contentFragment['type'], contentFragment['value'])

          for key in meta:
            if key != targetName:
              for val in meta[key]:
                self.setProperty(targetObj, key, val)
          

  def read (self, meta, body):
    if 'type' in meta and meta['type']:
      for contentType in meta['type']:
        if contentType in self.contentTypes:
          contentFragment = self.makeContentFragment(contentType, body)
          self.makeLinks(meta, contentFragment)

          # return obj

    return None

class Command(BaseCommand):
  args = ''
  help = 'Generate a static interpretation of the pads'

  def handle(self, *args, **options):
    outputdir = os.path.join(BASE_DIR, 'ethertoff', 'static', 'generated')

    if os.path.exists(outputdir):
      shutil.rmtree(outputdir)
    
    os.mkdir(outputdir)
     

    parser = Parser()
    epclient = None


    for pad in Pad.objects.all():
      if not epclient:
        epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)

      name, extension = os.path.splitext(pad.display_slug)
      padID = pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(PAD_NAMESPACE_SEPARATOR, '_'))
      source = epclient.getText(padID)['text']

      if extension in ['.md', '.markdown']:
        md = markdown.Markdown(extensions=['extra', 'meta', TocExtension(baselevel=2), 'attr_list'])
        body = mark_safe(md.convert(source))
        
        meta = md.Meta
        parser.read(meta, body) 
      print('Read {}'.format(pad.display_slug))

    print('Read pads')
    print('Generating output')

    output(os.path.join(outputdir, 'produsers.html'), 'generated/produsers.html', { 'produsers': sorted(parser.data['produser'], key=lambda r: r['key']) })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
