from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
# Make sure contentTypes are registered before the form is loaded
import generator.local_models
from generator.collection import knownContentTypes as knownGeneratorContentTypes

contentTypes = knownGeneratorContentTypes()
templateChoices = [('none', _("No template"))] + list(zip(contentTypes, map(str.title, contentTypes)))

class PadCreate(forms.Form):
    name = forms.CharField(label=_("Name"))
    group = forms.CharField(widget=forms.HiddenInput)
    template = forms.ChoiceField(label=_("Template"), choices=templateChoices)


class GroupCreate(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('permissions',)
