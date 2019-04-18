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

# List pads
# Go through them, record information
# Feed content to templates


def output (path, template, context):
  with open(path, 'w', encoding='utf-8') as w:
    w.write(loader.render_to_string(template, context))

class Parser(object):
  def __init__ (self):
    self.linkTargets = ['produser', 'event']
    self.contentTypes = ['biography', 'bibliography', 'event', 'meeting', 'notes']

    self.data = { target: [] for target in self.linkTargets }
    self.index = { target: {} for target in self.linkTargets }

  def findTarget (self, targetName, key):
    if targetName in self.data:
      if key in self.index[targetName]:
        return self.index[targetName][key]
      else:
        target = { 'key': key }
        self.data[targetName].append(target)
        self.index[targetName][key] = target
        
    return target
  def makeContentFragment (self, contentType, body):
    ## Could be more intricate later on
    return { 'type': contentType, 'body': body }

  def makeLinks(self, meta, contentFragment):
    for targetName in self.linkTargets:
      if targetName in meta:
        for target in meta[targetName]:
          targetObj = self.findTarget(targetName, target)

          if contentFragment['type'] not in targetObj:
            targetObj[contentFragment['type']] = []

          targetObj[contentFragment['type']].append(contentFragment['body'])

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

    print('Read pads')
    print('Generating output')

    output(os.path.join(outputdir, 'produsers.html'), 'generated/produsers.html', { 'produsers': parser.data['produser'] })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
