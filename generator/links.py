import random
from .utils import debug, keyFilter
from .collection import collectionFor


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
  def __init__ (self, target, contentType, inline=False, direct=False, source=None, label=None):
    self.target = target # Target [Model|key]
    self.contentType = contentType # ContentType of the target
    self.inline = inline # True when instantiated from wihtin in a body text
    self._id = ''.join([str(random.randint(0,9)) for x in range(15)]) # random unique id
    self.label = label # Display label
    self.reverse_link = None # Reference to the revers link
    self.context = None
    
    if direct and source:
      self.resolved = True
      self.source = source
      self.broken = False
    else:
      self.resolved = False
      self.source = None
      self.broken = False
    
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
    self.original = link

  @property
  def id (self):
    return 'l' + str(self._id)
    # return keyFilter('{1}-{0}-{2}'.format(self.source, self.target, self._id))

  def __repr__ (self):
    return 'Reverse link of {} <- {}'.format(repr(self.source), repr(self.target))

  def __str__ (self):
    return str(self.target)

  @property
  def context (self):
    return self.original.context

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

  def __bool__ (self):
    return True if self.value else False

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
  
  def __bool__ (self):
    return (len(self.value) > 0)

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

  def __bool__ (self):
    return (len(self.value) > 0)

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
