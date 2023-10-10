from django.conf import settings
from etherpadlite.models import Pad
from ethertoff.utils import getPadMarkdown, discover_root_folders, getPadBySlug, pathToSlugPrefix
import os.path
import json

def load_labels ():
  try:
    labels = json.load(open(os.path.join(settings.BACKUP_DIR, 'index-labels.json'), 'r'))
  except IOError:
    labels = {}

  return labels


def store_labels (labels):
  json.dump(labels, open(os.path.join(settings.BACKUP_DIR, 'index-labels.json'), 'w'), ensure_ascii=False)


def index_labels():
  root_folders = discover_root_folders()
  # Todo, make indexing recursive and link it to a folder
  labels = {}

  for folder in root_folders:
    folder_labels_pad = getPadBySlug(pathToSlugPrefix([ folder ]) + settings.LABEL_PAD)

    if folder_labels_pad:
      text = getPadMarkdown(folder_labels_pad)
      labels[folder] = list(filter(lambda label: True if label else False, map(str.strip, text.split('\n'))))
  
  root_labels_pad = getPadBySlug(settings.LABEL_PAD)

  if root_labels_pad:
    text = getPadMarkdown(root_labels_pad)
    labels['root'] = list(filter(lambda label: True if label else False, map(str.strip, text.split('\n'))))
  else:
    labels['root'] = []
  
  store_labels(labels)

  return labels