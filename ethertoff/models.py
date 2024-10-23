from django.conf import settings
from django.db.models.functions import Lower
from django.urls import reverse
from etherpadlite.models import Pad

from ethertoff.utils import  ethertoff_directory, ethertoff_pad, ethertoff_path

class EthertoffDirectory (object):
    def __init__ (self, name, slug, path):
        self.name = name
        self.slug = slug
        self.path = path

    @property
    def url (self):
        if len(self.path) > 0:  
            return reverse('manage', args=[self])
        else:
            return reverse('manage')

    def __str__ (self):
        return self.name

    def toSlug (self):
        return self.path.toSlug() + settings.PAD_NAMESPACE_SEPARATOR + self.name

    def toPrefix (self):
        return self.toSlug() + settings.PAD_NAMESPACE_SEPARATOR

    @property
    def pads (self):
        return ethertoff_pad().objects.filter(display_slug__startswith=self.toPrefix()).order_by(Lower('display_slug'))


class EthertoffPath (object):
    def __init__ (self, path):
        self.separator = settings.PAD_NAMESPACE_SEPARATOR

        if path:
            if isinstance(path, list):
                self.parts = path
            else:
                self.parts = self.parseSlug(path)
        else:
            self.parts = []

    def parseSlug (self, slug):
        parts = []

        for name in slug.split(self.separator):
          # This is quite recursive :-/
          parts.append(ethertoff_directory()(name, name, ethertoff_path()([p for p in parts])))

        return parts

    def toSlug (self):
        return self.separator.join(map(lambda p: p.slug, self.parts))

    def __len__ (self):
        return len(self.parts)

    def __getitem__ (self, item):
        return self.parts[item]

    # def split (self):
    #     return (EthertoffPath(self.parts[:-1]), self.parts[-1])


class EthertoffPad (Pad):
    class Meta:
      proxy = True

    def parseDisplaySlug(self):
        raw_path, label = self.display_slug.rsplit(settings.PAD_NAMESPACE_SEPARATOR, 1)
        # @FIXME, look into into proper terms.
        # Current interpretation feels clunky
        self._path = ethertoff_path()(raw_path)
        self._label = label

    @property
    def path (self):
      if not hasattr(self, '_path'):
        self.parseDisplaySlug()
      return self._path
    
    @property
    def url(self):
        return reverse('pad-write', args=[self])
    
    @property
    def label (self):
        if not hasattr(self, '_label'):
            self.parseDisplaySlug()
        
        return self._label

    def __str__ (self):
        return self.label