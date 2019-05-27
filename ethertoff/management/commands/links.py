from .models import collectionFor

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
        raise LinkExistsError
    else:
      links = getattr(obj, self.linkName)
    
    links.append(target)
    
    setattr(obj, self.linkName, links)

def is_link (obj):
  return isinstance(obj, (Link, MultiLink, ReverseLink, ReverseMultiLink))
