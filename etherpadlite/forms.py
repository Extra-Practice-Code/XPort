from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
# Make sure contentTypes are registered before the form is loaded


class PadCreate(forms.Form):
    name = forms.CharField(label=_("Name"))
    folder = forms.CharField(label=_("Folder"), required=False)
    group = forms.CharField(widget=forms.HiddenInput)


class GroupCreate(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('permissions',)
