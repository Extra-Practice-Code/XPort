from django import forms
from generator import PUBLICATION_STATE_HIDDEN, PUBLICATION_STATE_PUBLIC, PUBLICATION_STATE_UNPUBLISHED

publication_mode_choices = ['design', 'archive']
publication_state_choices = [PUBLICATION_STATE_HIDDEN, PUBLICATION_STATE_PUBLIC, PUBLICATION_STATE_UNPUBLISHED]

def makeGenerationForm (publications, post=None, initial={}):
    class GenerationForm (forms.Form):
        def __init__ (self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for publication in publications:
                self.fields[publication] = forms.ChoiceField(
                    choices=zip(publication_mode_choices, publication_mode_choices),
                    required=False,
                    initial=initial[publication] if publication in initial else None    
                )

    return GenerationForm(post)

class PublicationGenerationForm (forms.Form):
    publication_slug = forms.CharField(widget=forms.HiddenInput)
    organisation_slug = forms.CharField(widget=forms.HiddenInput)
    next_state = forms.ChoiceField(
        widget=forms.HiddenInput,
        choices=zip(publication_state_choices, publication_state_choices),
        required=False
    )
    mode = forms.ChoiceField(
        widget=forms.HiddenInput,
        choices=zip(publication_mode_choices, publication_mode_choices),
        required=False
    )