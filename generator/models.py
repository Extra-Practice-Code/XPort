from . import fields
from .utils import debug, CMAGENTA, keyFilter, try_attributes, render_to_string
import os.path
import re
import random
# from .internallinks import resolveInternalLinks
# from .links import Link, MultiLink, ReverseLink, ReverseMultiLink, is_link

from functools import partial

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

"""
  The link object, the link field will in the end be filled with these
"""
class Link (object):
  def __init__ (self, source, target):
    self.source = source
    self.target = target
    self._id = ''.join([str(random.randint(0,9)) for x in range(15)])

  def __repr__ (self):
    return 'Link between {} -> {}'.format(repr(self.source), repr(self.target))

  def __str__ (self):
    return str(self.target)

  @property
  def id (self):
    return '{}-{}-{}'.format(self.source, self.target, self._id)

  def link (self):
    try:
      return self.target.link
    except:
      print('****')
      print('BROKEN LINK')
      print(self.source, self.target, self.id)

"""
  Field for a links, holds more information, like the contenttype and whether
  a reverse link shoudl be put in place.
"""
class LinkField(object):
  def __init__ (self, contentType, reverse=None):
    self.contentType = contentType
    self.reverse = reverse # Reverse function with the soure object
 
  def __call__ (self, targetLabel): 
    contentType = self.contentType
    reverse = self.reverse

    def create(source):
      collection = collectionFor(contentType)
      target = collection.get(label=targetLabel)

      if reverse and target:
        reverse(target, source)

      return Link(source, target)

    return create
    
"""
  Field for multiple links.
"""
class MultiLinkField(LinkField):
  def __call__ (self, targetLabels):
    debug('Link target keys', targetLabels, color=CMAGENTA)
    contentType = self.contentType
    reverse = self.reverse

    def link (source):
      collection = collectionFor(contentType)
      # filter(None, x) Filters out empty string keys
      targets = [ collection.get(label=targetLabel) for targetLabel in filter(None, targetLabels) ]

      if reverse:
        for target in filter(None, targets):
          reverse(target, source)

      return [ Link(source, target) for target in targets ]

    return link

# This could as well be a partial?
class ReverseLinkField(object):
  def __init__ (self, name):
    self.linkName = name
  
  def __call__ (self, source, target):
    if hasattr(source, self.linkName):
      raise LinkExistsError()
    
    setattr(source, self.linkName, Link(source, target))  

class ReverseMultiLinkField(ReverseLinkField):
  def __call__ (self, source, target):
    if hasattr(source, self.linkName):
      links = getattr(source, self.linkName)
      if type(links) is not list:
        raise LinkExistsError
    else:
      links = []
    

    if target not in links:
      links.append(target)
    
    setattr(source, self.linkName, links)

def is_link (obj):
  return isinstance(obj, (LinkField, MultiLinkField, ReverseLinkField, ReverseMultiLinkField))

def linkMultiReverse(contentType, reverseName):
  return LinkField(contentType=contentType, reverse=ReverseMultiLinkField(reverseName))

def multiLinkMultiReverse(contentType, reverseName):
  return MultiLinkField(contentType=contentType, reverse=ReverseMultiLinkField(reverseName))

def linkReference(target, display_label):
  return '<a href="{target}" class="{className}">{label}</a>'.format(label=display_label if display_label else str(target), target=target.link, className=target.contentType)

def includeVideo(video, display_label):
  return render_to_string('snippets/video.html', { 'video': video })

def includeAudio(audio, display_label):
  return render_to_string('snippets/audio.html', { 'audio': audio })

def includeImage(image, display_label):
  return '<img src="{}" />'.format(image.image)

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

  return '<span class="tag" id="{id}">{label}</span>'.format(label=display_label if display_label else str(tag), id=link.id)

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

def parseReference(match, collector=None, source=None):
  contentType = match.group(1).strip().lower()
  label = match.group(2).strip()
  metadata, display_label = parseReferenceMetadata(match.group(3)) if match.group(3) else (None, None)
  print()
  print()
  print('*** Parsing reference')
  print(contentType, label, metadata, display_label)

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

        print('FOUND TARGET', target)

        # Here we should create the link between the source and the target
        # setattr(source, contentType, target)
        link = Link(source, target)
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
  return re.sub(r'\[((?:\d+(?:h|:))?(?:\d+:)?\d+)\]', insertTimecode, content)

def expandTags (content):
  return re.sub(r'\[\[\s*([^:\]]+)\s*\]\]', '[[tag: \\1]]', content)

def resolveReferences (content, model=None, source=None):
  # return content
  collector = [] # Collects all the targets
  if content:
    content = expandTags(content) # Rewrite short form tags into longform [[tagname]] → [[tag: tagname]]
    content = parseShortTimecodes(content)
    content = parseTimecodes(content)
    return (mark_safe(re.sub(r'\[\[([\w\._\-]+):([^\|\]]+)(?:\|(.[^\]+]+))?\]\]', partial(parseReference, collector=collector, source=source), content)), collector)
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

  def __init__ (self, key=None, label=None, metadata={}, content=None, source_path=None):
    debug('Instantiating model of type {}, key: {}, label: {}'.format(self.contentType, key, label))
    self.metadata = {}
    
    if key: 
      self.key = key
    else:
      self.key = self.extractKey(metadata)

    if label and not self.labelField in metadata:
      print('Setting label!')
      self.__setattr__(self.labelField, label)

    if metadata:
      self.setMetadata(metadata)

    if source_path:
      self.source_path = source_path

    self.stub = True

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
      self.stub = False
      self.setMetadata(metadata)
    if content:
      self.stub = False
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
      self.metadata[name] = self.metadataFields[name](value)
    else:
      # This might not be the best idea?
      self.metadata[name] = value

  def resolveLinks(self):
    print('Resolving links')
    for fieldname in self.metadata:
      print(fieldname, callable(fieldname))
      if callable(self.metadata[fieldname]):
        result = self.metadata[fieldname](self)
        self.metadata[fieldname] = result

  def __getattr__ (self, name):
    if name in self.metadata:
      return self.metadata[name]
    elif name.lower() != name:
      name = re.sub('[A-Z]', lambda m: '-{}'.format(m.group(0).lower()), name)
      return self.__getattr__(name)
    else:
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
        debug('Updating metadata for stub {}'.format(obj.key))
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
    if not key:
      key = keyFilter(label)

    if self.has(key):
      # debug('Found entry for {}'.format(key))
      return self.index[key]
    else:
      return self.instantiate(key=key, label=[label])


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
    if not callable(self.event):
      return self.event[0].target.link + '#' + self.key
    else:
      return ''

  metadataFields = {
    'date': fields.Single(fields.DateField()),
    'end_date': fields.Single(fields.DateField()),
    'time': fields.Single(fields.TimeField()),
    'produser': multiLinkMultiReverse('produser', 'events'),
    'participant': multiLinkMultiReverse('produser', 'events_participant'),
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
    'sortname': fields.Single(fields.StringField()),
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
    'participant': multiLinkMultiReverse('produser', 'notes_participant'),
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
    'caption': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'video'),
    'produser': multiLinkMultiReverse('produser', 'video'),
  }

class Audio (Model):
  contentType = 'audio'
  keyField = 'audio'
  labelField = 'audio'

  metadataFields = {
    'audio': fields.Single(fields.StringField()),
    'type': fields.Single(fields.StringField()),
    'title': fields.Single(fields.InlineMarkdownField()),
    'caption': fields.Single(fields.InlineMarkdownField()),
    'tags': multiLinkMultiReverse('tag', 'audio'),
    'produser': multiLinkMultiReverse('produser', 'audio'),
  }

class Image (Model):
  contentType = 'image'
  keyField = 'image'
  labelField = 'image'

  metadataFields = {
    'image': fields.Single(fields.StringField()),
    'tags': multiLinkMultiReverse('tag', 'image'),
    'produser': multiLinkMultiReverse('produser', 'image'),
    'title': fields.Single(fields.InlineMarkdownField()),
    'caption': fields.Single(fields.InlineMarkdownField()),
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
    'event': ContentType(Event),
    'programme-item': ContentType(ProgrammeItem),
    'produser': ContentType(Produser),
    'trajectory': ContentType(Trajectory),
    'pad': ContentType(Pad),
    'page': ContentType(Page),
    'tag': ContentType(Tag, InstantiatingCollection),
    'bibliography': ContentType(Bibliography, InstantiatingCollection),
    'video': ContentType(Video, InstantiatingCollection),
    'audio': ContentType(Audio, InstantiatingCollection),
    'image': ContentType(Image, InstantiatingCollection),
    'text': ContentType(Text),
    'notes': ContentType(Note),
    'external-project': ContentType(ExternalProject, InstantiatingCollection),
    'question': ContentType(Question, InstantiatingCollection)
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
