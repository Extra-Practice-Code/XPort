import random
from select import EPOLLEXCLUSIVE
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
  def __init__ (self, source, target, contentType, inline=False, direct=False, label=None, data = None):
    self.target = target # Target [Model|key]
    self.contentType = contentType # ContentType of the target
    self.inline = inline # True when instantiated from wihtin in a body text
    self._id = ''.join([str(random.randint(0,9)) for x in range(15)]) # random unique id
    self.label = label # Display label
    self.reverse_link = None # Reference to the revers link
    self.context = None
    self.data = data
    self.source = source
    
    if direct and source:
      self.resolved = True
      self.broken = False

      # Set data on target object if it's a stub
      if self.data and self.target.stub:
        self.target.fill(data)

    else:
      self.resolved = False
      self.broken = False
    
    self.reverse = False

  def __repr__ (self):
    return 'Link between {} ({}) -> {} ({})'.format(str(self.source), self.source.contentType, str(self.target), self.target.contentType)

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

  # @FIXME, the link might also register itself here?
  def resolve (self):
    if self.target and not self.resolved:
      debug(self.target, self.contentType)
      target = collectionFor(self.contentType).get(self.target, label=self.label)
      if target:
        self.target = target

        # Set data on target object if it's a stub
        if self.data and self.target.stub:
          self.target.fill(self.data)

      else:
        self.broken = True
        debug('Broken link', self.source, target)
      
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
    self.contentType = self.target.contentType
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
  def __init__ (self, source, contentType, reverse=None):
    self.contentType = contentType
    self.resolved = False
    self.value = None
    # Reference to the model the field is registered on
    self.source = source
    # Will hold the label / key of the target.
    # Once resolved the link is stored in value
    self.reverse = reverse
 
  def __str__ (self):
    return str(self.value)

  def __bool__ (self):
    return True if self.value else False

  def resolve (self):
    if self.value:
      self.value.resolve()
      self.resolved = True
      # Should we also resolve the reverse link?
      if not self.value.broken and self.reverse is not None:
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
  def set (self, target, label=None, data=None, inline=False):
    if type(target) is list:
      self.set(target[0], label, data, inline)
    else:
      targetKey = keyFilter(target)

      if not label:
        label = targetKey

      if targetKey:
        link = Link(self.source, targetKey, self.contentType, inline=inline, label=target, data=data)
        self.value = link
        # Add link to model
        self.source.registerLink(link)

  # Directly construct a link
  # Circumvents the resolving through a collection
  def makeLink(self, target, inline=False, label=None, data=None):
    if not self.resolved:
      link = Link(self.source, target, self.contentType, inline=inline, direct=True, label=label, data=None)
      self.value = link
      # Add link to model
      self.source.registerLink(link)
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
  
  @property
  def link (self):
    if self.value:
      return self.value

"""
  Field for multiple links, every link will be a single linkfield.
"""
class MultiLinkField(object):
  def __init__ (self, source, contentType = None, reverse = None, unique = True):
    self.contentType = contentType
    self.value = []
    self.source = source
    self.reverse = reverse
    self.unique = unique

  # By default the link targets are returned
  # to loop through the links, use the `links` property
  def __iter__ (self):
    return iter(self.targets)
  
  def __bool__ (self):
    return (len(self.value) > 0)

  def set (self, target, label=None, data=None, inline=False):
    if type(target) is list:
      for t in target:
        self.set(t, label, data, inline)
    else:
      targetKey = keyFilter(target)
      if targetKey:
        if not self.unique \
          or all([existingLink.target != targetKey and existingLink.target != target for existingLink in self.value]):
          link = Link(self.source, targetKey, self.contentType, inline=inline, label=target, data=data)
          self.value.append(link)
          # Add link to model
          self.source.registerLink(link)

  def makeLink(self, target, inline=False, label=None, data=None):
    if self.unique:
      for existingLink in self.value:
        if existingLink.target == target:
          return existingLink

    link = Link(self.source, target, self.contentType, inline, direct=True, label=label, data=data)
    self.value.append(link)
    # Add link to model
    self.source.registerLink(link)
    
    if self.reverse is not None:
      self.reverse.resolve(ReverseLink(link))

    return link
  
  # def resolveLink

  def resolve (self):
    for link in self.value:
      link.resolve()
      if not link.broken and self.reverse is not None:
        self.reverse.resolve(ReverseLink(link))

  @property
  def targets (self):
    return [link.target for link in self.value]

  @property
  def links (self):
    return self.value

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
    # Add link to model
    link.source.registerLink(link)
  
  @property
  def target (self):
    if self.value:
      return self.value.target

  @property
  def link (self):
    if self.value:
      return self.value

class ReverseMultiLinkField(ReverseLinkField):
  def __init__ (self, name, unique=True):
    self.name = name
    self.value = []
    self.id = ''.join([str(random.randint(0, 9)) for r in range(3)])
    self.unique = unique

  def __iter__ (self):
    return iter(self.targets)

  
  def resolve (self, link):
    # If there is not yet a field on the source create it,
    # otherwise append the link to the existing field
    """
      @FIXME checks whether the field exists in metadatat.
      While attributions set when the pad is parsed are set
      directly on the class.

      When the propery is being read, it's not looked up on the
      metadata dictionary, but the class itself.

      Allowing for two attributes to co-exist.
    """
    if self.name not in link.source.metadata:
      ## Every time make sure a new container is created
      link.source.registerMetadataField(self.name, ReverseMultiLinkField(self.name))
    else:
      # UNIQUE LINK UNIQUE_LINK
      # Check whether there is already a link to this target
      # on source, for now don't set it if this is the case.
      if self.unique:
        for exisitingLink in link.source.metadata[self.name].value:
          if is_link(exisitingLink) or is_reverse_link(exisitingLink):
            if exisitingLink.target == link.target:
              # This link already exists, for now we ignore it.
              return False

    link.source.metadata[self.name].value.append(link)
    # Add link to model
    link.source.registerLink(link)
    
  @property
  def targets (self):
    return [link.target for link in self.value]
  
  @property
  def links (self):
    return self.value

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

def linkReverse(source, contentType, reverseName):
  return LinkField(source=source, contentType=contentType, reverse=ReverseLinkField(reverseName))

def linkMultiReverse(source, contentType, reverseName):
  return LinkField(source=source, contentType=contentType, reverse=ReverseMultiLinkField(reverseName))

def multiLinkMultiReverse(source, contentType, reverseName, unique=True):
  return MultiLinkField(source=source, contentType=contentType, reverse=ReverseMultiLinkField(reverseName, unique=unique), unique=unique)

def multiLinkReverse (source, contentType, reverseName, unique=True):
  return MultiLinkField(source=source, contentType=contentType, reverse=ReverseLinkField(reverseName), unique=unique)

def linkReference(target, display_label):
  return '<a href="{target}" class="{className}">{label}</a>'.format(label=display_label if display_label else str(target), target=target.link, className=target.contentType)
