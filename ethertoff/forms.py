from django import forms
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.validators import UnicodeUsernameValidator

class ContactForm(forms.Form):
    name         = forms.CharField(max_length=50, label=_("First Name"))
    email        = forms.EmailField(label=_("E-Mail"))
    subject      = forms.CharField(max_length=100, label=_("Subject"))
    message      = forms.CharField(widget=forms.Textarea(), label=_("Message"))

class RenameFolderForm(forms.Form):
    old_name = forms.CharField(label=_("Old name"), required=False)
    new_name = forms.CharField(label=_("New name"), required=False)

class RenamePadForm(forms.Form):
    pk = forms.HiddenInput()
    old_name = forms.CharField(label=_("Old name"), required=False)
    new_name = forms.CharField(label=_("New name"))

