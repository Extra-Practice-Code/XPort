from etherpadlite.forms import PadCreate
from django import forms
from django.utils.translation import ugettext_lazy as _


# def templateChoices ():
#   templatePads = selectPadsByPath(['Templates'])

#   return [('none', _("No template"))] + [
#     (pad.name, pad.display_slug) for pad in templatePads
#   ]

class PadCreateWithTemplate (PadCreate):
  template = forms.ChoiceField(label=_("Template"), choices=[])