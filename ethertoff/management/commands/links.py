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
  
  def __call__ (self, source, destination):
    if hasattr(source, self.linkName):
      raise LinkExistsError()
    
    setattr(source, self.linkName, destination)  

class ReverseMultiLink(ReverseLink):
  def __call__ (self, source, destination):
    if hasattr(source , self.linkName):
      links = getattr(source, self.linkName)

      if type(links) is not list:
        raise LinkExistsError
    else:
      links = getattr(source, self.linkName)
    
    links.append(destination)
    
    setattr(source, self.linkName, links)

def is_link (obj):
  return isinstance(obj, (Link, MultiLink, ReverseLink, ReverseMultiLink))
