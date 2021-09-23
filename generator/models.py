from . import fields
from .utils import debug, warn, CMAGENTA, keyFilter, try_attributes, render_to_string
import os.path
import re
import random
from collections import OrderedDict
# from .internallinks import resolveInternalLinks
# from .links import Link, MultiLink, ReverseLink, ReverseMultiLink, is_link

from functools import partial

from django.utils.safestring import mark_safe

from generator.settings import SITE_URL

VIMEO_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:player\.|www\.)?vimeo\.com\/(?:video\/)?(\d+)', re.I)

from string import ascii_letters, digits

def make_id (length):
  tokens = ascii_letters + digits
  return ''.join([random.choice(tokens) for _ in range(15)])

"""
  - Alternatively: make and register models before parsing their fields.
    Then unknown resources / objects are easier to spot.

  - Make links more complex objects in result, so we can find the source
    reference: how to make those links 'stable'

  The result of a reference depends the type, many objects will result
  in a link, while some will result in a tag.
"""
class UnknownContentTypeError(Exception):
  def __init__(self, contentType):
    self.contentType = contentType

  def __str__(self):
    return 'Unknown contenttype `{}`'.format(self.contentType)

class LinkExistsError(Exception):
  pass # TODO: implement

# This error should be raised when an object is added
# to a reverse container with a different contentType.
# ContentTypes should be homogenous
class LinkDifferentContentTypeError(Exception):
  pass 

# class LinkStub (object):
#   def __init__ (self, target):
#     self.target = target

"""
  The link object, the link field will in the end be filled with these
"""
class Link (object):
  def __init__ (self, target, contentType, inline=False, direct=False, source=None, label=None):
    self.target = target
    self.contentType = contentType
    self.inline = inline
    self._id = ''.join([str(random.randint(0,9)) for x in range(15)])
    self.label = label
    
    if direct and source:
      self.resolved = True
      self.source = source
      self.broken = False
    else:
      self.resolved = False
      self.source = None
      self.broken = False
    
    # Flag whether this a reverse link
    self.reverse = False

  def __repr__ (self):
    return 'Link between {} -> {}'.format(repr(self.source), repr(self.target))

  def __str__ (self):
    return str(self.target)

  @property
  def id (self):
    return 'l' + str(self._id)
    # return keyFilter('{0}-{1}-{2}'.format(self.source, self.target, self._id))

  def link (self):
    try:
      return self.target.link
    except:
      debug('****')
      debug('BROKEN LINK')
      debug(self.source, self.target, self.id)

  def resolve (self, source):
    if self.target and not self.resolved:
      debug(self.target, self.contentType)
      self.source = source
      target = collectionFor(self.contentType).get(self.target, label=self.label)
      if target:
        self.target = target
      else:
        self.broken = True
        debug('Broken link', source, target)
      
      self.resolved = True
    elif not self.target:
      self.broken = True

"""
  Takes a link on initiation and reverses it, while keeping the original id.
  Allowing to track it across the platform.
"""
class ReverseLink (object):
  def __init__ (self, link):
    self._id = link._id
    self.source = link.target
    self.target = link.source
    self.inline = link.inline
    self.reverse = True
    self.resolved = link.resolved
    self.broken = link.broken
    self.label = link.label

  @property
  def id (self):
    return 'l' + str(self._id)
    # return keyFilter('{1}-{0}-{2}'.format(self.source, self.target, self._id))

  def __repr__ (self):
    return 'Reverse link of {} <- {}'.format(repr(self.source), repr(self.target))

  def __str__ (self):
    return str(self.target)

"""
  Field for a links, holds more information, like the contenttype and whether
  it has, and the type of reverse link.
"""
class LinkField(object):
  def __init__ (self, contentType, reverse=None):
    self.contentType = contentType
    self.resolved = False
    self.value = None
    # Will hold the label / key of the target.
    # Once resolved the link is stored in value
    self.reverse = reverse
 
  def __str__ (self):
    return str(self.value)

  def resolve (self, source):
    if self.value:
      self.value.resolve(source)
      self.resolved = True
      # Should we also resolve the reverse link?
      if not self.value.broken and self.reverse:
        # If so provide a reversed version of the link
        self.reverse.resolve(ReverseLink(self.value))
    else:
      debug('Unset linkfield')
    # if self.target and not self.resolved:
    #   print(self.target, self.contentType)
    #   target = collectionFor(self.contentType).get(self.target)
    #   if target:
    #     self.makeLink(source, target)
    #   else:
    #     debug('Broken link', source, target)
      
    #   self.resolved = True

  # Takes a string for target
  # boolean whether this an inline link
  def set (self, target, inline=False):
    if type(target) is list:
      self.set(target[0], inline)
    else:
      key = keyFilter(target)
      self.value = Link(key, self.contentType, inline, label=target)

  # Directly construct a link
  # Circumvents the resolving through a collection
  def makeLink(self, source, target, inline=False, label=None):
    if not self.resolved:
      link = Link(target, self.contentType, inline, True, source, label=label)
      self.value = link
      # if we have a reverse link, set it
      if self.reverse:
        self.reverse.resolve(ReverseLink(link))
      self.resolved = True

      return link
    
  #   return None

  @property
  def target (self):
    if self.value:
      return self.value.target

"""
  Field for multiple links, every link will be a single linkfield.
"""
class MultiLinkField(object):
  def __init__ (self, contentType = None, reverse = None, unique = True):
    self.contentType = contentType
    self.value = []
    self.target = None
    self.reverse = reverse
    self.unique = unique

  def __iter__ (self):
    return iter(self.value)

  def set (self, target, inline=False):
    if type(target) is list:
      for t in target:
        self.set(t, inline)
    else:
      key = keyFilter(target)
      if self.unique:
        for existingLink in self.value:
          if existingLink.target == key or existingLink.target == target:
            return existingLink

      self.value.append(Link(key, self.contentType, inline, label=target))

  def makeLink(self, source, target, inline=False, label=None):
    if self.unique:
      for existingLink in self.value:
        if existingLink.target == target:
          return existingLink

    link = Link(target, self.contentType, inline, direct=True, source=source, label=label)
    self.value.append(link)

    if self.reverse:
      self.reverse.resolve(ReverseLink(link))

    return link
  
  # def resolveLink

  def resolve (self, source):
    for link in self.value:
      link.resolve(source)
      if not link.broken and self.reverse:
        self.reverse.resolve(ReverseLink(link))

  @property
  def targets (self):
    return [link.target for link in self.value]

# This could as well be a partial?
class ReverseLinkField(object):
  def __init__ (self, name):
    self.name = name
    self.value = None

  def __str__ (self):
    return str(self.value)

  def resolve (self, link):
    self.value = link
    # Register the reverse link on the target.
    # this is a problem. The multilinkfield will have
    # linkfields in the iterator, rather than links.
    # Simplify?
    link.source.registerMetadataField(self.name, self)
  
  @property
  def target (self):
    if self.value:
      return self.value.target

class ReverseMultiLinkField(ReverseLinkField):
  def __init__ (self, name, unique=True):
    self.name = name
    self.value = []
    self.id = ''.join([str(random.randint(0, 9)) for r in range(3)])
    self.unique = unique

  def __iter__ (self):
    return iter(self.value)

  def resolve (self, link):
    # If there is not yet a field on the source create it,
    # otherwise append the link to the existing field
    if self.name not in link.source.metadata:
      ## Every time make sure a new container is created
      link.source.registerMetadataField(self.name, ReverseMultiLinkField(self.name))
    else:
      # UNIQUE LINK UNIQUE_LINK
      # Check whether there is already a link to this target
      # on source, for now don't set it if this is the case.
      if self.unique:
        for exisitingLink in link.source.metadata[self.name].value:
          if exisitingLink.target == link.target:
            # This link already exists, for now we ignore it.
            return False

    link.source.metadata[self.name].value.append(link)

  @property
  def targets (self):
    return [link.target for link in self.value]

# Returns true id the given object is a LinkField
# or a MultiLinkField
def is_link (obj):
  return isinstance(obj, (LinkField, MultiLinkField))

# Returns true if the given object is a LinkField
def is_single_link (obj):
  return isinstance(obj, (LinkField,))

def is_multi_link (obj):
  return isinstance(obj, (MultiLinkField,))

def is_reverse_link (obj):
  return isinstance(obj, (ReverseLinkField, ReverseMultiLinkField))

def is_reverse_single_link (obj):
  return isinstance(obj, (ReverseLinkField,))

def is_reverse_multi_link (obj):
  return isinstance(obj, (ReverseMultiLinkField,))

def linkReverse(contentType, reverseName):
  return LinkField(contentType=contentType, reverse=ReverseLinkField(reverseName))

def linkMultiReverse(contentType, reverseName):
  return LinkField(contentType=contentType, reverse=ReverseMultiLinkField(reverseName))

def multiLinkMultiReverse(contentType, reverseName, unique=True):
  return MultiLinkField(contentType=contentType, reverse=ReverseMultiLinkField(reverseName, unique=unique), unique=unique)

def linkReference(target, display_label):
  return '<a href="{target}" class="{className}">{label}</a>'.format(label=display_label if display_label else str(target), target=target.link, className=target.contentType)

def includeVideo(video, display_label):
  return render_to_string('snippets/video.html', { 'video': video })

def includeAudio(audio, display_label):
  return render_to_string('snippets/audio.html', { 'audio': audio })

def includeImage(image, display_label):
  return render_to_string('snippets/image.html', { 'image': image })
  # return '<img src="{}" />'.format(image.image)

def includeQuestion(question, display_label):
  return render_to_string('snippets/question.html', { 'question': question })

def includeExternalProject(project, display_label):
  return '<a href="{}" class="external-project">{}</a>'.format(try_attributes(project, ['link', 'project']), display_label if display_label else project.project)

def includeTag(tag, display_label, source, link):
  # if model:
  #   try:
  #     if tag not in model.tags:
  #       model.tags.append(tag)
  #   except AttributeError:
  #     model.tags = [tag]
  # print('<span class="tag" id="{id}">{label}</span>'.format(label=display_label if display_label else str(tag), id=link.id))
  return '<a class="tag" id="{id}" href="{url}">{label}</a>'.format(label=display_label if display_label else str(tag), id=link.id, url=tag.link)

def labelReference(target, display_label):
  return '<span class="{}">{}</span>'.format(target.contentType, display_label if display_label else str(target))

def renderReference(target, display_label, source, link):
  if target.contentType == 'video':
    return includeVideo(target, display_label)
  elif target.contentType == 'audio':
    return includeAudio(target, display_label)
  elif target.contentType == 'image':
    return includeImage(target, display_label)
  elif target.contentType == 'question':
    return includeQuestion(target, display_label)
  elif target.contentType == 'external-project':
    return includeExternalProject(target, display_label)
  elif target.contentType == 'bibliography':
    return labelReference(target, display_label)
  elif target.contentType == 'tag':
    return includeTag(target, display_label, source, link)
  else:
    return linkReference(target, display_label)

# def insertReference(matches):
#   contentType = matches.group(1)
#   key = matches.group(2)
#   target = collectionFor(contentType).get(key)

#   return target.reference

def parseReferenceMetadata (raw):
  data = {}

  # Split into metadata and display label
  # print('Raw metadata ', raw)
  if ':' in raw:
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


def resolveContentType(attr, model):
  if attr in model.metadata and (is_link(model.metadata[attr])):
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
  debug()
  debug()
  debug('*** Parsing reference')
  debug(contentType, label, metadata, display_label)

  if label:
    try:
      target = collectionFor(contentType).get(label=label)

      # debug('Metadata in reference: {}, source: {}'.format(metadata, match.group(0)))
      # debug('Rendered reference ', renderReference(target))

      if target:
        if metadata and target.stub:
          # Insert the metadata on the object ?
          # If the target has been instantiated by the collection
          # fill it with the metadata that was inserted on the reference
          target.fill(metadata)

        debug("Found target '{}' of type '{}'".format(target, contentType))

        if referenceName in source.metadata and is_link(source.metadata[referenceName]):
          ## FIXME what if it's an existing reverse
          link = source.metadata[referenceName].makeLink(source, target, inline=True, label=display_label)
        elif referenceName + 's' in source.metadata and is_multi_link(source.metadata[referenceName + 's']):
          ## FIXME what if it's an existing reverse?
          link = source.metadata[referenceName + 's'].makeLink(source, target, inline=True, label=display_label)
        else:
          link = None

        # Here we should create the link between the source and the target
        # setattr(source, contentType, target)
        # if target.contentType in source.metadata and is_link(source.metadata[target.contentType]):
        #   ## FIXME what if it's an existing reverse
        #   link = source.metadata[target.contentType].makeLink(source, target, inline=True, label=display_label)
        # elif target.contentType + 's' in source.metadata and is_multi_link(source.metadata[target.contentType + 's']):
        #   ## FIXME what if it's an existing reverse?
        #   link = source.metadata[target.contentType + 's'].makeLink(source, target, inline=True, label=display_label)
        # else:
        #   link = None

        # link = Link(source, target)
        collector.append(target)

        return renderReference(target, display_label=display_label, source=source, link=link)
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

def expandTags (content):
  return re.sub(r'\[\[\s*([^:\]]+)\s*\]\]', '[[tag: \\1]]', content)

def resolveReferences (model):
  # return content
  collector = [] # Collects all the targets
  content = model.content
  if content:
    content = expandTags(content) # Rewrite short form tags into longform [[tagname]] → [[tag: tagname]]
    content = parseShortTimecodes(content)
    content = parseTimecodes(content)
    return (mark_safe(re.sub(r'\[\[([\w\._\-]+):([^\|\]]+)(?:\|(.[^\]+]+))?\]\]', partial(parseReference, collector=collector, source=model), content)), collector)
    # return mark_safe(re.sub(r"\[\[(\w+):(.[^\]]+)\]\]", insertReference, content))
  else:
    return (content, [])

class Model(object):
  content = None
  source_path = None
  keyField = 'id'
  labelField = 'title'
  # metadata = OrderedDict()
  
  def __init__ (self, key=None, label=None, metadata={}, content=None, source_path=None):
    debug('Instantiating model of type {}, key: {}, label: {}'.format(self.contentType, key, label))
    self.metadata = OrderedDict()

    for fieldName, field in self._metadataFields().items():
      self.metadata[fieldName] = field

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

    if metadata or content:
      self.fill(metadata=metadata, content=content)

    self._id = make_id(15)
  
  @classmethod
  def extractKey(cls, data):
    if cls.keyField in data:
      return keyFilter(data[cls.keyField])
    elif 'pk' in data:
      return keyFilter(data['pk'])
    else:
      raise ValueError("Object doesn't have any key")

  @property
  def link (self):
    return os.path.join(SITE_URL, self.prefix, '{}.html'.format(self.key))

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

  def __setattr__ (self, name, value):
    if name == 'metadata':
      super().__setattr__(name, value)
    elif name in self.metadata:
      self.metadata[name].set(value)
    else:
      super().__setattr__(name, value)

  def registerMetadataField (self, fieldName, field):
    if fieldName not in self.metadata:
      self.metadata[fieldName] = field

  def resolveLinks(self):
    debug('Resolving links')
    debug(self.contentType)
    # print(self.metadata, 'key: ', self.key)
    fields = list(self.metadata.keys())
    for fieldname in fields:
      if is_link(self.metadata[fieldname]):
        self.metadata[fieldname].resolve(self)
      # print(fieldname, callable(fieldname))
      # if callable(self.metadata[fieldname]):
      #   result = self.metadata[fieldname](self)
      #   self.metadata[fieldname] = result

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

  @property
  def label (self):
    return self.metadata[self.labelField]

  # @property
  # def key (self):
  #   return self.metadata[self.keyField]

  # @property
  # def content (self):
  #   return self._content

  # @content.setter
  # def contentSetter (self, content):
  #   self._content = content

  def __dir__ (self):
    return list(self.metadata.keys()) + ['content', 'link', 'source_path']

class Collection(object):
  def __init__ (self, model):
    self.model = model
    self.models = []
    self.index = {}
    self.iterindex = -1# Maybe simplify to a function
# class InlineLink(Field):
#   def __init__ (self, target, label):
#     self.target = target
#     self.label = label

#   def __str__  (self):
#     # return '[{}]({}){{: .{}}}'.format(self.label, self.target.link, self.target.contentType)
#     return '<a href="{target}" class="{className}">{label}</a>'.format(label=self.label, target=self.target.link, className=self.target.contentType)

  # def __iter__ (self):
  #   return self

  # def __next__ (self):
  #   self.iterindex = self.iterindex + 1
  
  #   if len(self.models) >= self.iterindex:
  #     raise StopIteration
  #   else:
  #     return self.models[self.iterindex]

  """
    Retreive a model from the collection with the given label.
    If instantiate is set to true an empty model will be created.
  """
  def get (self, key = None, label = None):
    if not label and not key:
      raise(AttributeError('Can not retreive a model without a key or a label.'))
    elif not label:
      label = key
    elif not key:
      key = keyFilter(label)

    if self.has(key):
      # debug('Found entry for {}'.format(key))
      return self.index[key]
    else:
      return None

  def has (self, key):
    return key in self.index

  """
    Register the given model with the collection
  """
  def register (self, obj):
    if isinstance(obj, self.model):
      if not self.has(obj.key):
        self.models.append(obj)
        self.index[obj.key] = obj
      elif self.index[obj.key].stub:
        debug('Updating metadata for stub {} {}'.format(obj.key, obj.label.value))
        self.index[obj.key].setMetadata(obj.meta)
      else:
        # Extend the object here
        debug('Already have', obj, obj.key)
        
  """
    Instantiate a model for the given key, metadata and content
    and register it on the collection.
  """
  def instantiate (self, key, label=None, metadata={}, content=None, source_path=''):
    obj = self.model(key=key, label=label, metadata=metadata, content=content, source_path=source_path)
    # print('OBJECT: ', obj)
    self.register(obj)
    return obj

""" 
  Instantiates a model if it isn't part of the collection.
  Useful for objects like tags or questions
""" 
class InstantiatingCollection (Collection):
  def get (self, key = None, label = None):
    if not label and not key:
      raise(AttributeError('Can not retreive a model without a key or a label.'))
    # if not key:
    key = keyFilter(label)

    if self.has(key):
      # debug('Found entry for {}'.format(key))
      return self.index[key]
    else:
      if label:
        return self.instantiate(key=key, label=[label])
      else:
        return self.instantiate(key=key, label=[key])

class Image (Model):
  contentType = 'image'
  keyField = 'image'
  labelField = 'image'

  def _metadataFields (self):
    return {
      'image': fields.Single(fields.StringField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField()),
    }

class Audio (Model):
  contentType = 'audio'
  keyField = 'audio'
  labelField = 'audio'

  def _metadataFields (self):
    return {
      'audio': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['audio/mp3'])),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }

class Shore (Model):
  contentType = 'shore'
  keyField = 'shore'
  labelField = 'shore'

  def _metadataFields (self):
    return {
      'shore': fields.Single(fields.StringField()),
      'image': linkReverse('image', 'shore'),
    }

class Element (Model):
  contentType = 'element'
  keyField = 'element'
  labelField = 'element'

  def _metadataFields (self):
    return {
      'element': fields.Single(fields.StringField()),
    }

class Tool (Model):
  contentType = 'tool'
  keyField = 'tool'
  labelField = 'tool'

  def _metadataFields (self):
    return {
      'tool': fields.Single(fields.StringField()),
    }

class Location (Model):
  contentType = 'location'
  keyField = 'location'
  labelField = 'location'
  prefix = 'locations'

  def _metadataFields (self):
    return {
      'location': fields.Single(fields.StringField()),
    }

class Theme (Model):
  contentType = 'theme'
  keyField = 'theme'
  labelField = 'theme'

  def _metadataFields (self):
    return {
      'theme': fields.Single(fields.StringField()),
      'words': fields.StringField(),
    }

class Protocol (Model):
  contentType = 'protocol'
  keyField = 'protocol'
  labelField = 'protocol'
  prefix = 'protocols'

  def _metadataFields (self):
    return {
      'protocol': fields.Single(fields.StringField()),
      'location': linkMultiReverse('location', 'protocols'),
      'tools': multiLinkMultiReverse('tool', 'protocols'),
      'elements': multiLinkMultiReverse('element', 'protocols'),
      'themes': multiLinkMultiReverse('theme', 'protocols'),
      'shores': multiLinkMultiReverse('shore', 'protocols'),
    }

class Conversation (Model):
  contentType = 'conversation'
  keyField = 'conversation'
  labelField = 'conversation'
  prefix = 'conversations'

  def _metadataFields (self):
    return {
      'conversation': fields.Single(fields.StringField()),
      'person': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'address': fields.Single(fields.StringField()),
      'location': linkMultiReverse('location', 'conversations'),
      'tools': multiLinkMultiReverse('tool', 'conversations'),
      'elements': multiLinkMultiReverse('element', 'conversations'),
      'themes': multiLinkMultiReverse('theme', 'conversations'),
      'shores': multiLinkMultiReverse('shore', 'conversations'),
    }

class Demonstration (Model):
  contentType = 'demonstration'
  keyField = 'demonstration'
  labelField = 'demonstration'
  prefix = 'demonstrations'

  def _metadataFields (self):
    return {
      'demonstration': fields.Single(fields.StringField()),
      'person': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'address': fields.Single(fields.StringField()),
      'location': linkMultiReverse('location', 'demonstrations'),
      'tools': multiLinkMultiReverse('tool', 'demonstrations'),
      'elements': multiLinkMultiReverse('element', 'demonstrations'),
      'themes': multiLinkMultiReverse('theme', 'demonstrations'),
      'shores': multiLinkMultiReverse('shore', 'demonstrations'),
    }


class ContentType (object):
  def __init__ (self, model, collection = Collection):
    self.model = model
    self._collection = collection
    self.resetCollection()

  def resetCollection(self):
    self.collection = self._collection(self.model)

# Perhaps include the sort in the collection?
# Might also need to include the outputfolder here
# rather than on the model?
contentTypes = {
    'audio': ContentType(Audio, InstantiatingCollection),
    'image': ContentType(Image, InstantiatingCollection),
    'shore': ContentType(Shore, InstantiatingCollection),
    'element': ContentType(Element, InstantiatingCollection),
    'tool': ContentType(Tool, InstantiatingCollection),
    'location': ContentType(Location, InstantiatingCollection),
    'theme': ContentType(Location, InstantiatingCollection),
    'protocol': ContentType(Protocol),
    'conversation': ContentType(Conversation),
    'demonstration': ContentType(Demonstration)
  }

def knownContentTypes():
  return contentTypes.keys()

def knownContentType(contentType):
  return contentType in knownContentTypes()

def resetCollections (contentTypes):
  for c in contentTypes:
    contentTypes[c].resetCollection()
  
  return contentTypes

def collectionFor (contentType):
  if knownContentType(contentType):
    return contentTypes[contentType].collection
  else:
    raise UnknownContentTypeError(contentType)

def modelFor (contentType):
  if knownContentType(contentType):
    return contentTypes[contentType].model
  else:
    raise UnknownContentTypeError(contentType)
