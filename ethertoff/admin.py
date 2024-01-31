from django.contrib import admin
from ethertoff.models import EtherportOrganisation
from etherpadlite.models import PadGroup
from ethertoff.adminUtils import get_default_user_group, get_default_pad_server

@admin.register(EtherportOrganisation)
class EtherportOrganisationAdmin(admin.ModelAdmin):
  fields = ('name', 'slug', 'members')
  prepopulated_fields = {'slug': ('name',),}
  list_display = ('name', 'slug')

  # When an organisation is created create an associated PadGroup and attach.
  # Could also live in the model and / or in a signal.
  def save_model (self, request, obj, form, change):
    if not change:
      
      # First save the model
      super().save_model(request, obj, form, change)
    
      padGroup = PadGroup(
        group=get_default_user_group(),
        server=get_default_pad_server()
      )

      padGroup.save()
      
      obj.padGroup = padGroup
      obj.save()
