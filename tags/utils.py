from django.conf import settings
from etherpadlite.models import Pad
from ethertoff.utils import getPadMarkdown
import os.path
import json

def load_tags ():
  try:
    tags = json.load(open(os.path.join(settings.BACKUP_DIR, 'index.json'), 'r'))
  except IOError:
    tags = []

  return tags

def store_tags (tags):
  json.dump(tags, open(os.path.join(settings.BACKUP_DIR, 'index.json'), 'w'), ensure_ascii=False)

def index_tags():
  try:
    tagsPad = Pad.objects.get(display_slug=settings.TAG_PAD)
    text = getPadMarkdown(tagsPad)
    tags = list(filter(lambda tag: True if tag else False, map(str.strip, text.split('\n'))))

    store_tags(tags)

    return tags
  except Pad.DoesNotExist: # If there is no homepage defined we go to the login:
    return []