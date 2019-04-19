# -*- coding: utf-8 -*-

import urllib
import os
import os.path
import shutil


import markdown
from markdown.extensions.toc import TocExtension
from py_etherpad import EtherpadLiteClient

from django.template import loader
from django.template.defaultfilters import slugify
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
        'produser': FIELD_SINGLE,
        'role': FIELD_SINGLE,
        'biography': FIELD_SINGLE,
        'event': FIELD_ITERABLE,
        'trajectory': FIELD_SINGLE
      },
      'event': {
        'event': FIELD_SINGLE
      }
    }

    self.contentTypes = ['produser', 'bibliography', 'event', 'meeting', 'note', 'trajectory']

    self.data = { target: [] for target in self.contentTypes }
    self.index = { target: {} for target in self.contentTypes }


  def registerContentFragment (self, fragment):
    contentType = fragment['__type__']
    self.data[contentType].append(fragment)
    self.index[contentType][fragment['key']] = fragment
        

  def getFragment (self, contentType, key):
    if contentType in self.data:
      if key in self.index[contentType]:
        return self.index[contentType][key]
      else:
        target = self.makeContentFragmentSkeleton(contentType, key)
        self.registerContentFragment(target)
        
    return target

  def asKey(self, value):
    return slugify(value)

  def makeKey(self, contentType, value):
    # Possibly a lookup, for now look for propery in meta
    # with same name, else pick 'key' field
    if contentType in value:
      return self.asKey(value[contentType])
    elif 'key' in value:
      return self.asKey(value['key'])
    else:
      return value['pk']

  def makeContentFragmentSkeleton (self, contentType, key):
    return {
      '__type__': contentType,
      'key': key
    }

  def makeContentFragment (self, contentType, meta, body):
    key = self.makeKey(contentType, meta)
    fragment = self.getFragment(contentType, key)

    ## Could be more intricate later on
    for key in meta:
      if key != 'type' and key != 'key':
        if contentType in self.fields:
          if key in self.fields[contentType]:
            if self.fields[contentType][key] == FIELD_SINGLE:
              fragment[key] = meta[key][0]
            else:
              fragment[key] = meta[key]
          else:
              fragment[key] = meta[key]
        else:
          ## Possibly a filter for the metadata here ?
          fragment[key] = meta[key]

    fragment['body'] = body

    return fragment

  def insertLink (self, fragment, prop, target):
    # If there is a description for the property
    # follow the description: single or plural
    # to extend: overwrite / datafilter
    if target['__type__'] in self.fields:
      desc = self.fields[target['__type__']]
      if prop in desc:
        if desc[prop] == FIELD_SINGLE:
          target[prop] = fragment
        else:
          if prop not in target:
            target[prop] = []

          target[prop].append(fragment)

    else:
      if prop not in target:
        target[prop] = []

      target[prop].append(fragment)

  # Rename function
  def makeLinks(self, contentFragment):
    for prop in contentFragment:
      if prop != contentFragment['__type__'] and prop in self.contentTypes:
        key = self.asKey(contentFragment[prop])
        target = self.getFragment(prop, key)
        self.insertLink(contentFragment, contentFragment['__type__'], target)
        self.insertLink(target, prop, contentFragment)
          

  def read (self, meta, body):
    if 'type' in meta and meta['type']:
      for contentType in meta['type']:
        if contentType in self.contentTypes:
          contentFragment = self.makeContentFragment(contentType, meta, body)
          self.makeLinks(contentFragment)

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
    os.mkdir(os.path.join(outputdir, 'produsers'))
     

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
        try:
          meta = md.Meta
          meta['pk'] = pad.pk

          if meta['type'] == ['biography']:
            meta['type'] = ['produser']
        except:
          meta = { 'pk': pad.pk }
        parser.read(meta, body) 
      print('Read {}'.format(pad.display_slug))

    print('Read pads')
    print('Generating output')

    print(parser.data)
    output(os.path.join(outputdir, 'produsers.html'), 'generated/produsers.html', { 'produsers': sorted(parser.data['produser'], key=lambda r: r['key']) })

    for produser in parser.data['produser']:
      print('*****')
      print(produser['key'], produser['produser'])
      output(os.path.join(outputdir, 'produsers', '{}.html'.format(produser['key'])), 'generated/produser.html', { 'produser': produser })

    if not DEBUG:
      call_command('collectstatic', interactive=False)
