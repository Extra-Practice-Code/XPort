import os.path

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from etherpadlite.models import PadGroup
from ethertoff.models import EthertoffPath
from ethertoff.utils import pathToSlug
from generator import PUBLICATION_STATE_UNPUBLISHED
import json
from ethertoff.utils import  ethertoff_directory, ethertoff_path, ethertoff_pad

PUBLICATION_INDEX_PATH = os.path.join(settings.BACKUP_DIR, 'index-publications.json')


# [{ title: str, path: str, url: str }, ...]
def loadPublications ():
  try:
    publications = json.load(open(PUBLICATION_INDEX_PATH, 'r'))
  except IOError:
    publications = {}

  return publications

"""
  Try to get publication data like title and state from the publication index.
"""
def getPublicationData (organisation_slug, publication_slug, publication_index=None):
    if publication_index is None:
      publication_index = loadPublications()

    if organisation_slug in publication_index and publication_slug in publication_index[organisation_slug]:
        publicationData = publication_index[organisation_slug][publication_slug]
        publicationData['slug'] = publication_slug
        # @FIXME ethertoff_slug is ambiguous. 
        publicationData['ethertoff_slug'] = pathToSlug([ organisation_slug, publication_slug ])
    else:
        publicationData = {
            'path': publication_slug,
            'title': publication_slug,
            'slug': publication_slug,
              # @FIXME ethertoff_slug is ambiguous. 
            'ethertoff_slug': pathToSlug([ organisation_slug, publication_slug ]),
            'state': PUBLICATION_STATE_UNPUBLISHED
        }

    return publicationData  

class EtherportOrganisation (models.Model):
    class Meta ():
        db_table = "ethertoff_etherportorganisation"

    name = models.CharField(max_length=250)
    slug = models.SlugField()
    padGroup = models.ForeignKey(PadGroup, related_name='etherportOrganisation', on_delete=models.PROTECT, null=True)
    members = models.ManyToManyField(User, related_name='etherportOrganisations')

    def __str__(self):
        return self.name
    
    def url (self):
        return reverse('generator-list-publications') + f'#{self.slug}'


class EtherportPublication (object):
    def __init__ (self, organisation_slug, publication_slug, path=None, publication_index=None):
        data = getPublicationData(organisation_slug, publication_slug, publication_index)

        self.slug = data['slug']
        self.path = path
        self.title = data['title']
        self.state = data['state']
    
    @property
    def url (self):
      return reverse('manage', args=[self.toSlug()])
    
    def __str__ (self):
      return self.title

    def toSlug (self):
        return self.path.toSlug() + settings.PAD_NAMESPACE_SEPARATOR + self.slug

    def toPrefix (self):
        return self.toSlug() + settings.PAD_NAMESPACE_SEPARATOR

    @property
    def pads (self):
        return ethertoff_pad().objects.filter(display_slug__startswith=self.toPrefix()).order_by(Lower('display_slug'))

# Change how the path is parsed to parse first part of
# path as an organisation and the second as a publication
class EtherportPath (EthertoffPath):
    def parseSlug (self, slug):
        parts = []

        for name in slug.split(self.separator):
          if len(parts) == 0:
            organisation = EtherportOrganisation.objects.get(slug=name)
            parts.append(organisation)
          elif len(parts) == 1:
            parts.append(EtherportPublication(parts[0].slug, name, ethertoff_path()([p for p in parts])))
          else:
            # This is quite recursive :-/
            parts.append(ethertoff_directory()(name, name, ethertoff_path()([p for p in parts])))

        return parts
