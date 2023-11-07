from django import forms

publicationModeChoices = ['normal', 'development']

def makeGenerationForm (publications, post=None, initial={}):
    class GenerationForm (forms.Form):
        def __init__ (self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for publication in publications:
                self.fields[publication] = forms.ChoiceField(
                    choices=zip(publicationModeChoices, publicationModeChoices),
                    required=False,
                    initial=initial[publication] if publication in initial else None    
                )

    return GenerationForm(post)