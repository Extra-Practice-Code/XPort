from django.db import models
from django.contrib.auth.models import User
from etherpadlite.models import PadGroup

class EtherportOrganisation (models.Model):
  name = models.CharField(max_length=250)
  slug = models.SlugField()
  padGroup = models.ForeignKey(PadGroup, related_name='etherportOrganisation', on_delete=models.PROTECT, null=True)
  members = models.ManyToManyField(User, related_name='etherportOrganisations')

  def __str__(self):
    return self.name
