
from generator import links
from generator.utils import debug, error, make_id, warn, keyFilter, render_template_to_string
import re
from collections import OrderedDict
from generator.collection import UnknownContentTypeError, collectionFor, knownContentType
import os.path
from generator.settings import SITE_URL
from generator.fields import Field, Single
# from .internallinks import resolveInternalLinks
# from .links import Link, MultiLink, ReverseLink, ReverseMultiLink, is_link

from functools import partial

from django.utils.safestring import mark_safe


"""
  - Alternatively: make and register models before parsing their fields.
    Then unknown resources / objects are easier to spot.

  - Make links more complex objects in result, so we can find the source
    reference: how to make those links 'stable'

  The result of a reference depends the type, many objects will result
  in a link, while some will result in a tag.
"""

"""
  Parses the metadata set on a metadata entry
"""
def parseMetadataEntryWithMetadata (raw):
  data = {}
  
  if '|' in raw:
    # First extract the key
    # @FIXME why not a simple split here?
    m = re.match(r"""
      ^(?:\|?([^:\|]+)) # Key at the start
      (.+)$ # subsequent content
    """, raw, re.VERBOSE)

    if m:
      model_key = m.group(1).strip()
      raw_meta = m.group(2).strip()

      m = re.match(r"""
            ^(.+)$ # Metadata chunk
            (?:\|?([^:\|]+))# Label at the end
          """, raw_meta, re.VERBOSE)

      if m:
        raw_meta = m.group(1).strip()
        label = m.group(2).strip()
      else:
        label = model_key

      # Find data in raw metadata path
      for m in re.finditer(r'([\w\._-]+):\s*([^\|]+)\s*', raw_meta):
        key = m.group(1).strip()
        value = m.group(2).strip()

        if key not in data:
          data[key] = []
        
        data[key].append(value)
  else:
    model_key = raw
    label = raw

  return (model_key, data, label)

"""
  Parses meta data in inline references?

  contentType: id | key: value | key: value | display_label
"""
def parseReferenceMetadata (raw):
  data = {}

  # Test whether the string starts with metadata
  # @FIXME Stripping of metadata should be smoother
  if re.match(r'^\s*([\w\._-]+)\s*:\s*([^\|]+)\s*', raw):
    m = re.match(r'(.+)(?:\|?([^:\|]+))?$', raw)
    if m:
      raw_meta = m.group(1)
      label = m.group(2)

      for m in re.finditer(r'([\w\._-]+):([^\|]+)', raw_meta):
        key = m.group(1).strip()
        value = m.group(2).strip()

        if key not in data:
          data[key] = []
        
        data[key].append(value)
      
      return (data, label)
  
  return (None, raw.strip())


# Resolves content type for given attribute on given model
# if the attribute is not a link, or not registered on the model
# (can be the case on an inline reference) it'll try to look it
# it up in the contentTypes
def resolveContentType(attr, model):
  if attr in model.metadata and (links.is_link(model.metadata[attr])):
    return model.metadata[attr].contentType
  elif knownContentType(attr):
    return attr
  else:
    warn("Unknown contenttype '{}'".format(attr))
    return None

def parseReference(match, collector=None, source=None):
  referenceName = match.group(1).strip().lower()
  contentType = resolveContentType(referenceName, source) # match.group(1).strip().lower()
  label = match.group(2).strip()
  metadata, display_label = parseReferenceMetadata(match.group(3)) if match.group(3) else (None, None)
  debug('Parsing reference')
  debug(contentType, label, metadata, display_label)

  if label:
    try:
      target = collectionFor(contentType).get(label=label)

      # debug('Metadata in reference: {}, source: {}'.format(metadata, match.group(0)))
      # debug('Rendered reference ', renderReference(target))

      if target:
        # if metadata and target.stub:
        #   # Insert the metadata on the object ?
        #   # If the target has been instantiated by the collection
        #   # fill it with the metadata that was inserted on the reference
        #   target.fill(metadata)

        debug("Found target '{}' of type '{}'".format(target, contentType))

        # @FIXME references to contenttypes which do not have a (link)field are
        # not encoded as a link currently. Introduce an extra collector.
        if referenceName in source.metadata and links.is_link(source.metadata[referenceName]):
          ## FIXME what if it's an existing reverse
          link = source.metadata[referenceName].makeLink(target, inline=True, data=metadata, label=display_label)
        elif target.plural in source.metadata and links.is_multi_link(source.metadata[target.plural]):
          ## FIXME what if it's an existing reverse?
          link = source.metadata[target.plural].makeLink(target, inline=True, data=metadata, label=display_label)
        else:
          link = links.Link(source=source, target=target, contentType=contentType, inline=True, direct=True, data=metadata, label=display_label)

        # link = Link(source, target)
        if source:
          source.registerLink(link)

        collector.append(link)

        return target.asReference(display_label=display_label, source=source, link=link)

        # return renderReference(target, display_label=display_label, source=source, link=link)
      else:
        return label
    except UnknownContentTypeError:
      return match.group(0)
  else:
    debug('Skipping inline reference {}, no label'.format(match.group(0)))
    return match.group(0)

# difference between import and reference.
# Some reference result in a snippet of media

# would it make sense to have a sort of included media
# which can be extended by links in the 'metadata'

# [[video:]]

# switch between reference type and inclusion types

def formatTimecode(hours=None, minutes=None, seconds=None):
  out = '{1:0>2d}:{0:0>2d}'.format(int(seconds) if seconds else 0, int(minutes) if minutes else 0)
  
  if hours:
    out = '{:d}:{}'.format(int(hours), out) 
      
  return out

# Formats
# 7 → 7 seconds
# 7:00 → 7 minutes
# 1:07:00 → 1 hour, 7 minutes
# 1h7 → 1 hour, 7 minutes
def parseTimecodeString (content):
  if 'h' in content:
    hours, tail = content.split('h')

    if ':' in tail:
      minutes, seconds = tail.split(':', 2)
    else:
      minutes = tail
      seconds = 0
  else:
    parts = content.split(':', 3)

    if parts:
      if len(parts) == 3:
        hours, minutes, seconds = parts
      elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
      else:
        hours = 0
        minutes = 0
        seconds = parts[0]
    else:
      hours = 0
      minutes = 0
      seconds = 0

  return (int(hours), int(minutes), int(seconds))

def inSeconds(hours = 0, minutes = 0, seconds = 0):
  return max(0, seconds) + max(0, minutes * 60) + max(0, hours * 3600)

def insertTimecode (matches):
  hours, minutes, seconds = parseTimecodeString(matches.group(1))

  return '<span class="timecode" data-time="{0}">{1}</span>'.format(inSeconds(hours, minutes, seconds), formatTimecode(hours, minutes, seconds))

def parseTimecodes (content):
  return re.sub(r'\[\[t(?:imecode)?\s*:\s*([\d:]+)\]\]', insertTimecode, content)

def parseShortTimecodes (content):
  # return re.sub(r'(?<=[\s|^])\[((?:\d+(?:h|:))?(?:\d+:)?\d+)\]', insertTimecode, content)
  return re.sub(r'(?:(?<=\s)|(?<=^))\[((?:\d+(?:h|:))?(?:\d+:)?\d+)\](?:(?=\s)|(?=$))', insertTimecode, content)

def expandIfShort(match):
  if re.match(r'\[\[\s[\w\.\_\-]+:', match.group(0)):
    # Not a short tag
    return match.group(0)
  
  return re.sub(r'\[\[\s*([^:\]]+(?:\s*|\s*[^\]]+)?)\s*\]\]', '[[label: \\1]]', match.group(0))

def expandTags (content):
  return re.sub(r'\[\[\s*([^:\]]+(?:\s*|\s*[^\]]+)?)\s*\]\]', expandIfShort, content)

def resolveReferences (model):
  # return content
  collector = [] # Collects all the links
  content = model.content
  if content:
    content = expandTags(content) # Rewrite short form tags into longform [[tagname]] → [[tag: tagname]]
    content = parseShortTimecodes(content)
    content = parseTimecodes(content)
    # 
    referenceParser = partial(parseReference, collector=collector, source=model)
    referencePattern = r'\[\[\s*([\w\._\-]+)\s*:\s*([^\|\]]+)\s*(?:\|\s*(.[^\]+]+))?\s*\]\]'
    contentParsed = re.sub(referencePattern, referenceParser, content)

    # Add recognized references to the link collector of the model
    # Doing it here creates an unexpectedly ordered lists, as links to contentTypes
    # that are defined as a field are registered immediately.
    # for link in collector:
    #   model.registerLink(link)

    return (mark_safe(contentParsed), collector)
    # return mark_safe(re.sub(r"\[\[(\w+):(.[^\]]+)\]\]", insertReference, content))
  else:
    return (content, [])

class Model(object):
  content = None
  source_path = None
  keyField = None
  labelField = None
  prefix = None
  plural = None
  sortKey = None
  source_pad = None
  referenceTemplate = 'generator/snippets/references/reference.html'
  singlePageTemplate = 'generator/object.html'
  generateSinglePages = True
  listPageTemplate = 'generator/list.html'
  generateListPage = False
  context = {}

  def __init__ (self, key=None, label=None, metadata={}, content=None, source_path=None, source_pad=None, context={}):
    debug('Instantiating model of type {}, key: {}, label: {}'.format(self.contentType, key, label))
    self.metadata = OrderedDict(**self._metadataFields())
    
    if key: 
      self.key = key
    else:
      self.key = self.extractKey(metadata)

    if label and not self.labelField in metadata:
      debug('Setting label!', self.labelField)
      self.__setattr__(self.labelField, label)

    if source_path:
      self.source_path = source_path

    self.stub = True

    self.source_pad = source_pad

    self._id = make_id(15)

    self._links = []

    if metadata or content:
      self.fill(metadata=metadata, content=content)

    self.context = context

  """
    @FIXME 
  """
  def __setattr__ (self, name, value):
    # Trying to set the metadat attribute itself
    if name == 'metadata':
      super().__setattr__(name, value)
    elif name in self.metadata:
      # If the field being set is a link it might contain metadata itself.
      if isinstance(self.metadata[name], (links.LinkField, links.MultiLinkField)):
        if isinstance(value, list):
          for v in value:
            key, data, label = parseMetadataEntryWithMetadata(v)
            self.metadata[name].set(key, label=label, data=data)
        else:
          key, data, label = parseMetadataEntryWithMetadata(value)
          self.metadata[name].set(key, label=label, data=data)
      else:
        self.metadata[name].set(value)
    else:
      super().__setattr__(name, value)

  def __getattr__ (self, name):
    if name in self.metadata:
      return self.metadata[name]
    elif name.lower() != name:
      name = re.sub('[A-Z]', lambda m: '-{}'.format(m.group(0).lower()), name)
      return self.__getattr__(name)
    else:
      # super().__getattr__(name)
      debug('Attribute error', name)
      raise AttributeError()

  def __str__ (self):
    if hasattr(self, 'labelField') and hasattr(self, self.labelField):
      return str(getattr(self, self.labelField))
    elif hasattr(self, self.keyField):
      return str(getattr(self, self.keyField))
    else:
      debug('Has not attr for to string {}'.format(self.metadata))
      return super().__str__()

  def __dir__ (self):
    return list(self.metadata.keys()) + ['content', 'url', 'source_path', 'links']

  def _metadataFields (self):
    pass

  def setContext (self, context):
    self.context = context

  # @FIXME add a propery to loop through all linkfields
  # have a unified linklist? To loop through different contenttypes
  # in a single list

  @classmethod
  def extractKey(cls, data):
    if cls.keyField in data:
      return keyFilter(data[cls.keyField])
    elif 'pk' in data:
      return keyFilter(data['pk'])
    else:
      raise ValueError("Object doesn't have any key")

  # Should collect all links
  @property
  def links (self):
    return self._links

  @property
  def inlineLinks (self):
    return list(filter(self.links, lambda l: l.inline))

  def registerLink (self, link):
    if link not in self._links:
      self._links.append(link)

  @property
  def link (self):
    warn('Link property is outdated')
    return self.url

  @property
  def url (self):
    return os.path.join(self.context['SITE_URL'], self.prefix, '{}.html'.format(self.key))

  def setMetadata(self, metadata=None):
    if metadata:
      for key, value in metadata.items():
        self.__setattr__(key, value)

  # TODO: deal with objects which already have data
  # Overwrite or extend data. Etc.
  def fill(self, metadata={}, content=None, source_path=None):
    if metadata:
      self.stub = False
      self.setMetadata(metadata)
    if content:
      self.stub = False
      self.content = content
    if source_path:
      self.source_path = source_path

  def registerMetadataField (self, fieldName, field):
    if fieldName not in self.metadata:
      self.metadata[fieldName] = field

  def resolveLinks(self):
    debug('Resolving links of {} ({})'.format(self, self.contentType))
    fields = list(self.metadata.keys())
    for fieldname in fields:
      if links.is_link(self.metadata[fieldname]):
        self.metadata[fieldname].resolve()

  @property
  def label (self):
    return self.metadata[self.labelField]

  @property
  def fields (self):
    return self.metadata

  def asReference (self, display_label, source, link):
    return render_template_to_string(
      self.referenceTemplate,
      {
        'object': self,
        'label': display_label if display_label else self.label, # Label, set in the pad
        'source': source, # source (model), pad where the link is created
        'link': link  # link itself
      }
    ).replace('\n', ' ')

  def getSortKey (self):

    def getattrvalue (key):
      attr = getattr(self, key)

      if isinstance(attr, (Field, Single)):
        return attr.value
      else:
        return attr

    if self.sortKey:
      if isinstance(self.sortKey, tuple):
        sortKey = tuple(getattrvalue((key[1:] if key.startswith('-') else key)) for key in self.sortKey)
        return sortKey
      else:
        sortKeyField = self.sortKey[1:] if self.sortKey.startswith('-') else self.sortKey
        return getattrvalue(sortKeyField)
    else:
      return getattrvalue(self.labelField)

  @classmethod
  def getSortDirection (cls):
    return -1 if cls.sortKey and not isinstance(cls.sortKey, tuple) and cls.sortKey.startswith('-') else 1

  # @property
  # def key (self):
  #   return self.metadata[self.keyField]

  # @property
  # def content (self):
  #   return self._content

  # @content.setter
  # def contentSetter (self, content):
  #   self._content = content


