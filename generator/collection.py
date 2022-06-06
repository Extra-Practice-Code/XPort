from generator.utils import debug, keyFilter
from itertools import groupby

class UnknownContentTypeError(Exception):
  def __init__(self, contentType):
    self.contentType = contentType

  def __str__(self):
    return 'Unknown contenttype `{}`'.format(self.contentType)

class Collection(object):
  def __init__ (self, model):
    self.model = model
    self._models = []
    self.index = {}

  def __iter__ (self):
    return iter(self.models)

  """
    Retreive a model from the collection with the given label or key.
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
  def register (self, model):
    if isinstance(model, self.model):
      if not self.has(model.key):
        self._models.append(model)
        self.index[model.key] = model
      elif self.index[model.key].stub:
        debug('Updating metadata for stub {} with key {}'.format(model.key, model.label.value))
        self.index[model.key].setMetadata(model.meta)
      else:
        # Extend the object here
        debug('Already has {} with key {}'.format(model, model.key))
  
  def remove (self, model):
    if isinstance(model, self.model):
      if self.has(model.key):
        self._models.remove(model)
        del self.index[model.key]
  """
    Instantiate a model for the given key, metadata and content
    and register it on the collection.
  """
  def instantiate (self, key, label=None, metadata={}, content=None, source_path='', source_pad=None):
    model = self.model(key=key, label=label, metadata=metadata, content=content, source_path=source_path, source_pad=source_pad)
    self.register(model)
    return model

  @property
  def models (self):
    # Check whether sorted' copying bevahiour causes 
    return sorted(self._models, key = lambda m: m.getSortKey(), reverse=True if self.model.getSortDirection() < 0 else False)

  @property
  def grouped (self):
    return {k: list(v) for k, v in groupby(self.models, key=lambda m: getattr(m, m.groupKey).value)}

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

class ContentType (object):
  def __init__ (self, model, singlePages=True, prefix=None, collection = Collection):
    self.model = model
    self._collection = collection
    self.resetCollection()

  def resetCollection(self):
    self.collection = self._collection(self.model)


contentTypes = {}

def knownContentTypes():
  return contentTypes.keys()

def knownContentType(contentType):
  return contentType in knownContentTypes()

def resetCollections (contentTypes):
  for c in contentTypes:
    contentTypes[c].resetCollection()
  
  return contentTypes

def collectionFor (contentType):
  if contentType in contentTypes.keys():
    return contentTypes[contentType].collection
  else:
    raise UnknownContentTypeError(contentType)

def modelFor (contentType):
  if contentType in contentTypes.keys():
    return contentTypes[contentType].model
  else:
    raise UnknownContentTypeError(contentType)

# def registerContentType (model, collection):
#   contentTypes[model.contentType] = ContentType(model, collection)

def contentType (collection=Collection):
  def decorator (model):
    # debug("Registering content type {}".format(model.__name__.lower()))
    # Check whether the model has certain initial properties
    # if not, set default values
    if not hasattr(model, 'contentType') or not model.contentType:
      model.contentType = model.__name__.lower()

    if not hasattr(model, 'keyField') or not model.keyField:
      model.keyField = model.__name__.lower()

    if not hasattr(model, 'labelField') or not model.labelField:
      model.labelField = model.__name__.lower()

    if not hasattr(model, 'plural') or not model.plural:
      model.plural = '{}s'.format(model.__name__.lower())

    if not hasattr(model, 'prefix') or not model.prefix:
      model.prefix = model.plural

    contentTypes[model.contentType] = ContentType(model, collection=collection)
    return model
  
  return decorator

"""
  Returns an object with given contentType and key
"""
def getObject(contentType, key):
  collection = collectionFor(contentType)
  if contentType:
    return collection.get(key)
  return None