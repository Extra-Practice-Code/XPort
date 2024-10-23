PUBLICATION_STATE_PUBLIC = 'public'
PUBLICATION_STATE_HIDDEN = 'hidden'
PUBLICATION_STATE_UNPUBLISHED = 'unpublished'

ALLOWED_RESOURCE_NAMES = [ 'screen', 'print', 'common' ]


# class EtherportPath ():

class EtherportPublication (object):
  def __init__ (self, title, slug, path, state):
    self.path = path
    self.title = title
    self.slug = slug
    self.state = state


  def __str__ (self):
    return self.title