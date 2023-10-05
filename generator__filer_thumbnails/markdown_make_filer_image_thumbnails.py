from markdown import Extension
from markdown.treeprocessors import Treeprocessor
import re

DJANGO_FILER_CANONICAL_URL_PATTERN = re.compile(r'.*\/filer\/canonical\/\d+\/(\d+)\/$')

class MakeFilerImageThumbnails(Treeprocessor):
  def get_image_from_url (self, url):
    from filer.models import Image
    m = DJANGO_FILER_CANONICAL_URL_PATTERN.match(url)
    if m:
      pk = int(m.group(1))
      try:
        return Image.objects.get(pk=pk, is_public=True)
      except:
        return None

    else:
      return None
  def run(self, root):
    from easy_thumbnails.files import get_thumbnailer

    # Reverse looping, in case they are nested
    for el in list(root.findall(".//img"))[::-1]:
      imgSrc = el.get('src')

      if DJANGO_FILER_CANONICAL_URL_PATTERN.match(imgSrc):
        image = self.get_image_from_url(imgSrc)
        if image:
          try:
            thumbnailer = get_thumbnailer(image)
            thumb = thumbnailer.get_thumbnail({'size': (800, 1200)})
            el.set('src', thumb.url)
          except:
            pass

"""
  Loop through all image elements in parsed markdown and replace for a thumbnail.
"""
class MakeFilerImageThumbnailsExtension(Extension):
  def extendMarkdown(self, md):
    md.registerExtension(self)
    md.treeprocessors.register(MakeFilerImageThumbnails(md), 'makeFilerImageThumbnails', 5)