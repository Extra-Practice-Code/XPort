from . import fields
from .utils import info, debug, CMAGENTA, keyFilter, try_attributes
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

def linkReference(target):
  return '<a href="{target}" class="{className}">{label}</a>'.format(label=str(target), target=target.link, className=target.contentType)

def includeVideo(video):
  return '<video controls><source src="{}" type="{}"></video>'.format(video.video, video.type)

def includeAudio(audio):
  return '<audio controls><source src="{}" type="{}"></audio>'.format(audio.audio, audio.type)

def includeImage(image):
  return '<img src="{}" />'.format(image.image)

def includeQuestion(question):
  return '<span class="question">{}</span>'.format(question.question)

def includeExternalProject(project):
  return '<a href="{}" class="external-project">{}</a>'.format(try_attributes(project, ['link', 'project']), project.project)

def labelReference(target):
  return '<span class="{}">{}</span>'.format(target.contentType, str(target))

def renderReference(target):
  if target.contentType == 'video':
    return includeVideo(target)
  elif target.contentType == 'audio':
    return includeAudio(target)
  elif target.contentType == 'image':
    return includeImage(target)
  elif target.contentType == 'question':
    return includeQuestion(target)
  elif target.contentType == 'external-project':
    return includeExternalProject(target)
  elif target.contentType == 'bibliography':
    return labelReference(target)
  else:
    return linkReference(target)

# def insertReference(matches):
#   contentType = matches.group(1)
#   key = matches.group(2)
#   target = collectionFor(contentType).get(key)

#   return target.reference

def parseReferenceMetadata (raw):
  data = {}

  for m in re.finditer(r'([\w\._-]+):([^\|]+)', raw):
    key = m.group(1)
    value = m.group(2)

    if key not in data:
      data[key] = []
    
    data[key].append(value)
  
  return data

def parseReference(match, source=None):
  contentType = match.group(1).strip()
  label = match.group(2).strip()
  metadata = parseReferenceMetadata(match.group(3)) if match.group(3) else None
  target = collectionFor(contentType).get(label=label)

  debug('Metadata in reference: {}, source: {}'.format(metadata, match.group(0)))
  # debug('Rendered reference ', renderReference(target))

  # Insert the metadata on the object ?
  if metadata and target.empty:
    target.fill(metadata)


  if contentType == 'tag' and 'tags' in source.metadataFields:
    debug('Trying to extend tags')
    current = source.tags if hasattr(source, 'tags') else []
    if target not in current:
      source.tags = current + source.metadataFields['tags']([label], source)

  # return ''
  return renderReference(target)

# difference between import and reference.
# Some reference result in a snippet of media

# would it make sense to have a sort of included media
# which can be extended by links in the 'metadata'

# [[video:]]

# switch between reference type and inclusion types

def expandTags (content):
  return re.sub(r'\[\[([^:\]]+)\]\]', '[[tag: \\1]]', content)

def resolveReferences (content, source=None):
  # return content
  if content:
    return mark_safe(re.sub(r'\[\[([\w\._\-]+):([^\|\]]+)(?:\|(.[^\]+]+))?\]\]', partial(parseReference, source=source), expandTags(content)))
    # return mark_safe(re.sub(r"\[\[(\w+):(.[^\]]+)\]\]", insertReference, content))
  else:
    return content

class Model(object):
  metadataFields = {}
  _content = None
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
      self.content = resolveReferences(content, source=self)
    if source_path:
      self.source_path = source_path

  def __setattr__ (self, name, value):
    # This might break with the links
    if name in ['key', 'metadata', 'source_path']:
      super().__setattr__(name, value)
    elif name == 'content':
      super().__setattr__('_content', value)
    elif name in self.metadataFields:
      if is_link(self.metadataFields[name]):
        # If it is a link we also include, the obj
        self.metadata[name] = self.metadataFields[name](value, self)
      else:
        self.metadata[name] = self.metadataFields[name](value)
    else:
      self.metadata[name] = value

  def __getattr__ (self, name):
    if name in self.metadata:
      return self.metadata[name]
    else:
      # debug('Attribute error', name, self.metadata)
      raise AttributeError()

  def __str__ (self):
    if hasattr(self, 'labelField') and hasattr(self, self.labelField):
      return getattr(self, self.labelField)
    elif hasattr(self, self.keyField):
      return getattr(self, self.keyField)
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

  metadataFields = {
    'date': fields.Single(fields.DateField()),
    'end_date': fields.Single(fields.DateField()),
    'time': fields.Single(fields.TimeField()),
    'produser': multiLinkMultiReverse('produser', 'events'),
    'participant': multiLinkMultiReverse('produser', 'events_participant'),
    'event': fields.Single(fields.StringField()),
    'title': fields.Single(fields.StringField()),
    'summary': fields.Single(fields.MarkdownField()),
    'location': fields.Single(fields.StringField()),
    'address': fields.StringField(),
    'tags': multiLinkMultiReverse('tag', 'events'),
    'bibliography': multiLinkMultiReverse('bibliography', 'events'),
  }

class ProgrammeItem (Model):
  contentType = 'programme-item'

  metadataFields = {
    'date': fields.Single(fields.DateField()),
    'end_date': fields.Single(fields.DateField()),
    'time': fields.Single(fields.TimeField()),
    'produser': multiLinkMultiReverse('produser', 'events'),
    'participant': multiLinkMultiReverse('produser', 'events_participant'),
    'event': multiLinkMultiReverse('event', 'programmeItems'),
    'title': fields.Single(fields.StringField()),
    'summary': fields.Single(fields.MarkdownField()),
    'location': fields.Single(fields.StringField()),
    'address': fields.StringField(),
    'tags': multiLinkMultiReverse('tag', 'events'),
    'bibliography': multiLinkMultiReverse('bibliography', 'events'),
  }

class Produser (Model):
  contentType = 'produser'
  keyField = 'produser'
  labelField = 'produser'
  prefix = 'produsers'

  metadataFields = {
    'role': fields.Single(fields.StringField()),
    'name': fields.Single(fields.StringField()),
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
    'produser': linkMultiReverse('produser', 'pads'),
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
    'produser': linkMultiReverse('produser', 'notes'),
    'event': linkMultiReverse('event', 'notes'),
    'project-item': linkMultiReverse('project-item', 'notes'),
    'tags': multiLinkMultiReverse('tag', 'notes'),
    'bibliography': multiLinkMultiReverse('bibliography', 'notes'),
    'title': fields.Single(fields.StringField()),
  }

class Page (Model):
  contentType = 'page'
  keyField = 'title'
  labelField = 'title'
  prefix = 'pages'

  metadataFields = {
    'title': fields.Single(fields.StringField()),
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
    'bibliography': fields.Single(fields.StringField()),
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
    'title': fields.Single(fields.StringField()),
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
    'title': fields.Single(fields.StringField()),
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
    'title': fields.Single(fields.StringField()),
    'tags': multiLinkMultiReverse('tag', 'image'),
    'produser': multiLinkMultiReverse('produser', 'text'),
    'event': multiLinkMultiReverse('event', 'text')
  }

class Question (Model):
  contentType = 'question'
  keyField = 'question'
  labelField = 'question'

  metadataFields = {
    'question': fields.Single(fields.StringField())
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
