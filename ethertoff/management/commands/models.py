FIELD_DATE_FORMAT = '%d-%m-%Y'
FIELD_DATETIME_FORMAT = '%d-%m-%Y %H:%M'
FIELD_TIME_FORMAT = '%H:%M'

import datetime
import re
# from .links import Link, MultiLink, ReverseLink, ReverseMultiLink, is_link

import markdown
from django.utils.safestring import mark_safe

def keyFilter (value):
  if type(value) is list:
    return '--'.join([keyFilter(v) for v in value])
  elif type(value) is str:
    return re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', value.lower()))
  else:
    return value

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
class LinkDifferentContentType(Exception):
  pass 

class Link(object):
  def __init__ (self, contentType, reverse=None):
    self.contentType = contentType
    self.reverse = reverse
  
  def __call__ (self, targetKey, source):
    target = collectionFor(self.contentType).get(targetKey)
    if self.reverse:
      self.reverse(obj=target, target=source)
    return target

class MultiLink(Link):
  def __call__ (self, targetKeys, source):
    targets = [ collectionFor(self.contentType).get(targetKey) for targetKey in targetKeys ]

    if self.reverse:
      for target in targets:
        # Set the property
        self.reverse(source=target, target=source)

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
    if hasattr(target, self.linkName):
      links = getattr(obj, self.linkName)

      if type(links) is not list:
        # debug(self.linkName, obj.key, target.key, type(links))
        raise LinkExistsError
    else:
      links = []
    
    links.append(target)
    
    setattr(obj, self.linkName, links)

def is_link (obj):
  return isinstance(obj, (Link, MultiLink, ReverseLink, ReverseMultiLink))


class Model(object):
  metadataFields = {}
  content = None
  keyField = 'pk'
  metadata = {}
  
  def __init__ (self, key=None, metadata=None, content=None):
    print('Keyfield {}'.format(self.keyField))
    if key: 
      self.key = key
    else:
      self.key = keyFilter(metadata[self.keyField]) if self.keyField in metadata else keyFilter(metadata['pk']) if 'pk' in metadata else None
    self.metadata = {}
    if metadata:
      for key in metadata:
        self.__setattr__(key, metadata[key])
    
    if content:
      self.content = content

  def __setattr__ (self, name, value):
    # This might break with the links
    if name == 'key':
      super().__setattr__('key', value)
    elif name == 'metadata':
      super().__setattr__('metadata', value)
    elif name == 'content':
      super().__setattr__('content', value)
    elif name in self.metadataFields:
      print(name)
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
      raise AttributeError()

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
    self.iterindex = -1

  def __iter__ (self):
    return self

  def __next__ (self):
    self.iterindex = self.iterindex + 1
  
    if len(self.models) >= self.iterindex:
      raise StopIteration
    else:
      return self.models[self.iterindex]

  """
    Retreive a model from the collection with the given key.
    If instantiate is set to true an empty model will be created.
  """
  def get (self, key, instantiate=True):
    key = keyFilter(key)
    if key in self.index:
      return self.index[key]
    elif instantiate:
      return self.instantiate(key)
    else:
      return None

  """
    Register the given model with the collection
  """
  def register (self, obj):
    if isinstance(obj, self.model):
      if obj.key not in self.index:
        self.models.append(obj)
        self.index[obj.key] = obj

  """
    Instantiate a model for the given key, metadata and content
    and register it on the collection.
  """
  def instantiate (self, key, metadata=None, content=None):
    obj = self.model(key=key, metadata=metadata, content=content)
    self.register(obj)
    return obj

def dateField (value):
  return datetime.datetime.strptime(value, FIELD_DATE_FORMAT).date()

def dateTimeField (value):
  def parse (self, value):
    return datetime.datetime.strptime(value, FIELD_DATETIME_FORMAT)

def timeField (value):
  return datetime.datetime.strptime(value, FIELD_TIME_FORMAT).time()

def intField (value):
  return int(value)

def floatField(value):
  return float(value)

def stringField(value):
  return str(value)

def many(parse):
  return lambda val: [parse(v) for v in val] 

def single(parse):
  return lambda val: parse(val[0])

def markdownField(parse):
  md = markdown.Markdown(extensions=['extra', 'attr_list'])
  return mark_safe(md.convert(parse))

def linkMultiReverse(contentType, reverseName):
  return Link(contentType=contentType, reverse=ReverseMultiLink(reverseName))

class Event (Model):
  keyField = 'event'
  metadataFields = {
    'date': single(dateField),
    'produser': linkMultiReverse('produser', 'events'),
    'event': single(stringField),
    'summary': single(markdownField),
    'location': single(stringField),
    'address': many(stringField)
  }

class Produser (Model):
  keyField = 'produser'
  metadataFields = {
    'role': single(stringField),
    'produser': single(stringField),
    'tags': many(stringField)
  }

class Trajectory (Model):
  keyField = 'trajectory'
  metadataFields = {
    'produser': linkMultiReverse('produser', 'trajectories'),
    'tags': many(stringField)
  }

class Pad (Model):
  metadataFields = {
    'produser': linkMultiReverse('produser', 'pads'),
    'event': linkMultiReverse('events', 'pads'),
    'trajectory': linkMultiReverse('trajectory', 'pads'),
    'tags': many(stringField)
  }

class Page (Model):
  keyField = 'name'
  
contentTypes = {
  'event': { 'model': Event, 'collection': Collection(Event) },
  'produser': { 'model': Produser, 'collection': Collection(Produser) },
  'trajectory': { 'model': Trajectory, 'collection': Collection(Trajectory) },
  'pad': { 'model': Pad, 'collection': Collection(Pad) },
  'page': { 'model': Page, 'collection': Collection(Page) }
}

def collectionFor (contentType):
  if contentType in contentTypes:
    return contentTypes[contentType]['collection']
  else:
    raise UnknownContentTypeError(contentType)

def modelFor (contentType):
  if contentType in contentTypes:
    return contentTypes[contentType]['model']
  else:
    raise UnknownContentTypeError(contentType)