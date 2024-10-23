from django.conf import settings
from etherpadlite.models import Pad
from going_hybrid.models import EtherportOrganisation
from ethertoff.utils import getPadMarkdown, discoverFolders, getPadBySlug, pathToSlugPrefix
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
  # Todo, make indexing recursive and link it to a folder
  labels = {}

  for organisation in EtherportOrganisation.objects.all():
    organisation_labels = {}

    for folder in discoverFolders([ organisation.slug ]):
      folder_labels_pad = getPadBySlug(pathToSlugPrefix([ organisation.slug, folder ]) + settings.LABEL_PAD)

      if folder_labels_pad:
        text = getPadMarkdown(folder_labels_pad)
        organisation_labels[folder] = list(filter(lambda label: True if label else False, map(str.strip, text.split('\n'))))
    
    root_labels_pad = getPadBySlug(pathToSlugPrefix([ organisation.slug ]) + settings.LABEL_PAD)

    if root_labels_pad:
      text = getPadMarkdown(root_labels_pad)
      organisation_labels['root'] = list(filter(lambda label: True if label else False, map(str.strip, text.split('\n'))))
    else:
      organisation_labels['root'] = []

    labels[organisation.slug] = organisation_labels
  
  store_labels(labels)

  return labels