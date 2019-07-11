from . import fields
from .utils import info, debug, CMAGENTA, keyFilter, try_attributes, render_to_string
import os.path
import datetime
import re
# from .internallinks import resolveInternalLinks
# from .links import Link, MultiLink, ReverseLink, ReverseMultiLink, is_link

from functools import partial

import markdown
from django.utils.safestring import mark_safe

from generator.settings import SITE_URL

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

class Link(object):
  def __init__ (self, contentType, reverse=None):
    self.contentType = contentType
    self.reverse = reverse
  
  def __call__ (self, targetLabel, source): 
    debug('Link target {}'.format(targetLabel), color=CMAGENTA)
    if type(targetLabel) is list:
      targetLabel = targetLabel[0]

    target = collectionFor(self.contentType).get(label=targetLabel)
    if self.reverse:
      self.reverse(target, source)
    return target

class MultiLink(Link):
  def __call__ (self, targetLabels, source):
    debug('Link target keys', targetLabels, color=CMAGENTA)
    # Filter out empty string keys
    targets = [ collectionFor(self.contentType).get(label=targetLabel) for targetLabel in filter(None, targetLabels) ]

    if self.reverse:
      for target in targets:
        # Set the property
          self.reverse(target, source)

    return targets

# This couls as well be a partian
class ReverseLink(object):
  def __init__ (self, name):
    self.linkName = name
  
  def __call__ (self, obj, target):
    if hasattr(obj, self.linkName):
      raise LinkExistsError()
    
    setattr(obj, self.linkName, target)  

class ReverseMultiLink(ReverseLink):
  def __call__ (self, obj, target):
    if hasattr(obj, self.linkName):
      links = getattr(obj, self.linkName)
      if type(links) is not list:
        raise LinkExistsError
    else:
      links = []
    
    if target not in links:
      links.append(target)
    
    setattr(obj, self.linkName, links)

def is_link (obj):
  return isinstance(obj, (Link, MultiLink, ReverseLink, ReverseMultiLink))

def linkMultiReverse(contentType, reverseName):
  return Link(contentType=contentType, reverse=ReverseMultiLink(reverseName))

def multiLinkMultiReverse(contentType, reverseName):
  return MultiLink(contentType=contentType, reverse=ReverseMultiLink(reverseName))

def linkReference(target, display_label):
  return '<a href="{target}" class="{className}">{label}</a>'.format(label=display_label if display_label else str(target), target=target.link, className=target.contentType)

def includeVideo(video, display_label):
  return '<video controls><source src="{}" type="{}"></video>'.format(video.video, video.type)

def includeAudio(audio, display_label):
  return render_to_string('snippets/audio.html', { 'audio': audio })

def includeImage(image, display_label):
  return '<img src="{}" />'.format(image.image)

def includeQuestion(question, display_label):
  return render_to_string('snippets/question.html', { 'question': question })

def includeExternalProject(project, display_label):
  return '<a href="{}" class="external-project">{}</a>'.format(try_attributes(project, ['link', 'project']), display_label if display_label else project.project)

def labelReference(target, display_label):
  return '<span class="{}">{}</span>'.format(target.contentType, display_label if display_label else str(target))

def renderReference(target, display_label=None):
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
  print('Raw metadata ', raw)
  if ':' in raw:
    m = re.match(r'(.+)(?:\|?([^:\|]+))?$', raw)
    raw_meta = m.group(1)
    label = m.group(2)

    for m in re.finditer(r'([\w\._-]+):([^\|]+)', raw_meta):
      key = m.group(1).strip()
      value = m.group(2).strip()

      if key not in data:
        data[key] = []
      
      data[key].append(value)
    
    return (data, label)
  else:
    return (None, raw.strip())

def parseReference(match, collector=None):
  contentType = match.group(1).strip()
  label = match.group(2).strip()
  metadata, display_label = parseReferenceMetadata(match.group(3)) if match.group(3) else (None, None)

  try:
    target = collectionFor(contentType).get(label=label)

    debug('Metadata in reference: {}, source: {}'.format(metadata, match.group(0)))
    # debug('Rendered reference ', renderReference(target))

    # Insert the metadata on the object ?
    if metadata and target.empty:
      target.fill(metadata)

    collector.append(target)

    # if source and contentType == 'tag' and 'tags' in source.metadataFields:
    #   debug('Trying to extend tags')
    #   current = source.tags if hasattr(source, 'tags') else []
    #   if target not in current:
    #     source.tags = current + source.metadataFields['tags']([label], source)

    # return ''
    return renderReference(target, display_label=display_label)
  except UnknownContentTypeError:
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
  return re.sub(r'\[((?:\d+(?:h|:))?(?:\d+:)?\d+)\]', insertTimecode, content)

def expandTags (content):
  return re.sub(r'\[\[\s*([^:\]]+)\s*\]\]', '[[tag: \\1]]', content)

def resolveReferences (content, source=None):
  # return content
  collector = []
  if content:
    content = expandTags(content)
    content = parseShortTimecodes(content)
    content = parseTimecodes(content)
    return (mark_safe(re.sub(r'\[\[([\w\._\-]+):([^\|\]]+)(?:\|(.[^\]+]+))?\]\]', partial(parseReference, collector=collector), content)), collector)
    # return mark_safe(re.sub(r"\[\[(\w+):(.[^\]]+)\]\]", insertReference, content))
  else:
    return (content, [])

class Model(object):
  metadataFields = {}
  _content = None
  _source_path = None
  keyField = 'id'
  labelField = 'title'
  metadata = {}

  def __init__ (self, key=None, label=None, metadata=None, content=None):
    debug('Instantiating model of type {}, key: {}, label: {}'.format(self.contentType, key, label))
    self.metadata = {}
    
    if key: 
      self.key = key
    else:
      self.key = self.extractKey(metadata)

    if label:
      # debug('Setting label, {}, {}'.format(label, self.labelField))
      self.__setattr__(self.labelField, [label])

    if metadata:
      self.setMetadata(metadata)
    
    self.empty = True

    if metadata or content:
      self.fill(metadata=metadata, content=content)
  
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

  @property
  def content (self):
    return self._content

  @property
  def source_path (self):
    return self._source_path

  def setMetadata(self, metadata=None):
    if metadata:
      for key in metadata:
        self.__setattr__(key, metadata[key])

  # TODO: deal with objects which already have data
  # Overwrite or extend data. Etc.
  def fill(self, metadata={}, content=None, source_path=None):
    if metadata:
      self.empty = False
      self.setMetadata(metadata)
    if content:
      self.empty = False
      self.content = content
    if source_path:
      self.source_path = source_path

  def __setattr__ (self, name, value):
    # This might break with the links
    if name in ['key', 'metadata', 'empty']:
      super().__setattr__(name, value)
    elif name == 'content':
      super().__setattr__('_content', value)
    elif name == 'source_path':
      super().__setattr__('_source_path', value)
    elif name in self.metadataFields:
      if is_link(self.metadataFields[name]):
        # If it is a link we also include, the obj
        self.metadata[name] = self.metadataFields[name](value, self)
      else:
        self.metadata[name] = self.metadataFields[name](value)
    else:
      # This might not be the best idea?
      self.metadata[name] = value

  def __getattr__ (self, name):
    if name in self.metadata:
      return self.metadata[name]
    else:
      print(name)
      # super().__getattr__(name)
      # debug('Attribute error', name, self.metadata)
      raise AttributeError()

  def __str__ (self):
    if hasattr(self, 'labelField') and hasattr(self, self.labelField):
      return str(getattr(self, self.labelField))
    elif hasattr(self, self.keyField):
      return str(getattr(self, self.keyField))
    else:
      debug('Has not attr for to string {}'.format(self.metadata))
      return super().__str__()


  # @property
  # def content (self):
  #   return self._content

  # @content.setter
  # def contentSetter (self, content):
  #   self._content = content

  def __dir__ (self):
    return list(self.metadata.keys()) + ['content']

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
      debug('Found entry for {}'.format(key))
      return self.index[key]
    elif key:
      debug('Could not find entry for {}, instantiating'.format(key))
      return self.instantiateStub(key=key, label=label)
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
      elif self.index[obj.key].empty:
        debug('Updating metadata for stub {}'.format(obj.key))
        self.index[obj.key].setMetadata(obj.meta)
      else:
        # Extend the object here
        debug('Already have', obj, obj.key)
        
  """
    Instantiate a model for the given key, metadata and content
    and register it on the collection.
  """
  def instantiate (self, key, metadata=None, content=None):
    obj = self.model(key=key, metadata=metadata, content=content)
    self.register(obj)
    return obj

  def instantiateStub (self, key, label=None):
    obj = self.model(key=key, label=label)
    self.register(obj)
    return obj

class Event (Model):
  contentType = 'event'
  prefix = 'activities'
  labelField = 'title'

  metadataFields = {
    'date': fields.Single(fields.DateField()),
    'end_date': fields.Single(fields.DateField()),
    'time': fields.Single(fields.TimeField()),
    'produser': multiLinkMultiReverse('produser', 'events'),
    'participant': multiLinkMultiReverse('produser', 'events_participant'),
    'event': fields.Single(fields.StringField()),
    'title': fields.Single(fields.InlineMarkdownField()),
    'summary': fields.Single(fields.MarkdownField()),
    'location': fields.Single(fields.StringField()),
    'address': fields.StringField(),
    'tags': multiLinkMultiReverse('tag', 'events'),
    'bibliography': multiLinkMultiReverse('bibliography', 'events'),
    'image': fields.Single(fields.StringField()),
  }

class ProgrammeItem (Model):
  contentType = 'programme-item'
  labelField = 'title'

  def link (self):
    return self.event[0].link + '#' + self.key

  metadataFields = {
    'date': fields.Single(fields.DateField()),
    'end_date': fields.Single(fields.DateField()),
    'time': fields.Single(fields.TimeField()),
    'produser': multiLinkMultiReverse('produser', 'events'),
    'participants': multiLinkMultiReverse('produser', 'events_participant'),
    'event': multiLinkMultiReverse('event', 'programmeItems'),
    'title': fields.Single(fields.InlineMarkdownField()),
    'summary': fields.Single(fields.MarkdownField()),
    'location': fields.Single(fields.StringField()),
    'address': fields.StringField(),
    'tags': multiLinkMultiReverse('tag', 'events'),
    'bibliography': multiLinkMultiReverse('bibliography', 'events'),
  }

class Produser (Model):
  contentType = 'produser'
  keyField = 'produser'
  labelField = 'name'
  prefix = 'produsers'

  metadataFields = {
    'role': fields.Single(fields.StringField()),
    'name': fields.Single(fields.InlineMarkdownField()),
    'produser': fields.Single(fields.StringField()),
    'tags': multiLinkMultiReverse('tag', 'produsers'),
    'bibliography': multiLinkMultiReverse('bibliography', 'produsers'),
  }

class Trajectory (Model):
  contentType = 'trajectory'
  metadataFields = {
    'produser': linkMultiReverse('produser', 'trajectories'),
    'tags': multiLinkMultiReverse('tag', 'trajectories')
  }

class Pad (Model):
  contentType = 'pad'
  metadataFields = {
    'produser': multiLinkMultiReverse('produser', 'pads'),
    'event': linkMultiReverse('event', 'pads'),
    'trajectory': linkMultiReverse('trajectory', 'pads'),
    'tags': multiLinkMultiReverse('tag', 'pads'),
    'bibliography': multiLinkMultiReverse('bibliography', 'pads'),
  }

class Note (Model):
  contentType = 'note'
  labelField = 'title'
  prefix = 'notes'
  metadataFields = {
    'produser': multiLinkMultiReverse('produser', 'notes'),
    'participants': multiLinkMultiReverse('produser', 'notes_participant'),
    'event': linkMultiReverse('event', 'notes'),
    'programme-item': linkMultiReverse('programme-item', 'notes'),
    'tags': multiLinkMultiReverse('tag', 'notes'),
    'bibliography': multiLinkMultiReverse('bibliography', 'notes'),
    'title': fields.Single(fields.InlineMarkdownField()),
  }

class Page (Model):
  contentType = 'page'
  keyField = 'title'
  labelField = 'title'
  prefix = 'pages'

  metadataFields = {
    'title': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'pages'),
    'bibliography': multiLinkMultiReverse('bibliography', 'pages'),
  }

class Tag (Model):
  contentType = 'tag'
  keyField = 'tag'
  labelField = 'tag'
  prefix = 'tags'

  @property
  def link_count (self):
    count = 0
    
    debug(self.metadata)

    for field in self.metadata:
      if type(getattr(self, field)) is list:
        count += len(getattr(self, field))

    return count

  metadataFields = {
    'tag': fields.Single(fields.StringField())
  }

class Bibliography (Model):
  contentType = 'bibliography'
  keyField = 'bibliography'
  labelField = 'bibliography'

  metadataFields = {
    'bibliography': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'bibliography'),
    'produser': multiLinkMultiReverse('produser', 'bibliography')
  }

class Video (Model):
  contentType = 'video'
  keyField = 'video'
  labelField = 'video'
  
  metadataFields = {
    'video': fields.Single(fields.StringField()),
    'type': fields.Single(fields.StringField()),
    'title': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'video'),
    'produser': multiLinkMultiReverse('produser', 'video')
  }

class Audio (Model):
  contentType = 'audio'
  keyField = 'audio'
  labelField = 'audio'

  metadataFields = {
    'audio': fields.Single(fields.StringField()),
    'type': fields.Single(fields.StringField()),
    'title': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'audio'),
    'produser': multiLinkMultiReverse('produser', 'audio')
  }

class Image (Model):
  contentType = 'image'
  keyField = 'image'
  labelField = 'image'

  metadataFields = {
    'image': fields.Single(fields.StringField()),
    'tags': multiLinkMultiReverse('tag', 'image'),
    'produser': multiLinkMultiReverse('produser', 'image'),
    'caption': fields.Single(fields.StringField()),
  }

class ExternalProject (Model):
  contentType = 'external-project'
  keyField = 'project'
  labelField = 'project'

  metadataFields = {
    'project': fields.Single(fields.StringField()),
    'link': fields.Single(fields.StringField()),
    'tags': multiLinkMultiReverse('tag', 'externalProject'),
  }

class Text (Model):
  contentType = 'text'
  keyField = 'title'
  labelField = 'title'

  metadataFields = {
    'title': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'image'),
    'produser': multiLinkMultiReverse('produser', 'text'),
    'event': multiLinkMultiReverse('event', 'text')
  }

class Question (Model):
  contentType = 'question'
  keyField = 'question'
  labelField = 'question'

  metadataFields = {
    'question': fields.Single(fields.InlineMarkdownField())
  }

# Perhaps include the sort in the collection?
# Might also need to include the outputfolder here
# rather than on the model?
contentTypes = {
  'event': { 'model': Event, 'collection': Collection(Event) },
  'programme-item': { 'model': ProgrammeItem, 'collection': Collection(ProgrammeItem) },
  'produser': { 'model': Produser, 'collection': Collection(Produser) },
  'trajectory': { 'model': Trajectory, 'collection': Collection(Trajectory) },
  'pad': { 'model': Pad, 'collection': Collection(Pad) },
  'page': { 'model': Page, 'collection': Collection(Page) },
  'tag': { 'model': Tag, 'collection': Collection(Tag) },
  'bibliography': { 'model': Bibliography, 'collection': Collection(Bibliography) },
  'video': { 'model': Video, 'collection': Collection(Video) },
  'audio': { 'model': Audio, 'collection': Collection(Audio) },
  'image': { 'model': Image, 'collection': Collection(Image) },
  'text': { 'model': Text, 'collection': Collection(Text) },
  'notes': { 'model': Note, 'collection': Collection(Note) },
  'external-project': { 'model': ExternalProject, 'collection': Collection(ExternalProject) },
  'question': { 'model': Question, 'collection': Collection(Question) },
}

knownContentTypes = contentTypes.keys()

def collectionFor (contentType):
  if contentType in knownContentTypes:
    return contentTypes[contentType]['collection']
  else:
    raise UnknownContentTypeError(contentType)

def modelFor (contentType):
  if contentType in knownContentTypes:
    return contentTypes[contentType]['model']
  else:
    raise UnknownContentTypeError(contentType)
