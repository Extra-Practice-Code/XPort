from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from ethertoff.utils import pathToSlugPrefix
from etherpadlite.models import Pad

class PublicationForm(forms.Form):
    name = forms.CharField(label=_("Publication name"))
    
    def __init__ (self, *args, organisation_slug=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organisation_slug = organisation_slug

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        name = self.cleaned_data.get('name')

        prefix = pathToSlugPrefix([ self.organisation_slug, name ])
        pads = Pad.objects.filter(display_slug__startswith=prefix).order_by('name')

        if len(pads) > 0:
            self.add_error('name', ValidationError(_('%(name)s already exists'), params={'name': name} ))
