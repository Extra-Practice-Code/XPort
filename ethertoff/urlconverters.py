from ethertoff.utils import ethertoff_pad, ethertoff_path, ethertoff_directory

class DirectoryConverter:
    regex = "[\w\:\-\.]+"
    Directory = ethertoff_directory()
    Path = ethertoff_path()

    def to_python (self, value):
        return self.Path(value)[-1]

    def to_url(self, value):
        if hasattr(value, 'toSlug'):
          return value.toSlug() 
        else:
          return value
        # return value.toPrefix()
    

class PadConverter:
    regex = "[\w\:\-\.\_\?\,\!\&\\\"]+"
    Pad = ethertoff_pad()

    def to_python (self, value):
        try:
            return self.Pad.objects.get(display_slug=value)
        except self.Pad.DoesNotExist:
           raise ValueError

    def to_url(self, value):
        if isinstance(value, self.Pad):
          return value.display_slug
        else:
          return value
        # return value.toPrefix()
    