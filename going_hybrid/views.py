from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from ethertoff.models import EtherportOrganisation
from ethertoff.views import createPad
from ethertoff.utils import discoverPad, formatPad, getPadBySlug, slugToPath, pathToSlug, setPadText
from etherpadlite.models import Pad, PadAuthor
from going_hybrid.forms import PublicationForm, VisualStylesForm
from ethertoff.utils import pathToSlugPrefix, quickCleanPadname


@login_required(login_url='/accounts/login')
def create_visual_styles (request, prefix=None):
    prefix_path = slugToPath(prefix.strip(':'))

    if request.method == 'POST':
        form = VisualStylesForm(request.POST)

        if form.is_valid():        
            resources = {
                'css': ['common.css', 'screen.css', 'print.css'],
                'javascript': ['common.js', 'screen.js', 'print.js']
            }
            
            new_styles_base_path = prefix_path + [settings.THEME_LOCAL_FOLDERNAME]
        
            author = PadAuthor.objects.get(user=request.user)
            group = author.group.all()[0] # Change .all()[0] to .first() ?

            for (resource_type, resource_names) in resources.items():
                if form.cleaned_data[resource_type]:
                    for name in resource_names:
                        template_path = settings.THEME_DEFAULT_PATH + [ name ]
                        resource_path = new_styles_base_path + [ name ]
                        templatePad = getPadBySlug(pathToSlug(template_path))                        
                        pad = createPad(pathToSlug(resource_path), server=group.server, group=group, templatePad=templatePad)

                        if templatePad is None:
                            setPadText(pad, '')

            return redirect('manage', pathToSlug(new_styles_base_path))
    else:
        form = VisualStylesForm()

        context = {
            'form': form,
            'prefix': pathToSlug(prefix_path)
        }

    return render(request, 'going-hybrid/visual-styles-create.html', context)


@login_required(login_url='/accounts/login')
def create_publication (request, organisation_slug=None):
    if not organisation_slug:
        try:
            organisation = get_object_or_404(EtherportOrganisation, members__id=request.user.id)
        except EtherportOrganisation.MultipleObjectsReturned:
            return render(request, "going-hybrid/publication-create--pick-organisation.html", {
                'organisations': EtherportOrganisation.objects.filter(members__id=request.user.id)
            })
    else:
        organisation = get_object_or_404(EtherportOrganisation, slug=organisation_slug, members__id=request.user.id)
    
    if request.method == 'POST':
        form = PublicationForm(request.POST, organisation_slug=organisation.slug)

        if form.is_valid():
            publication_prefix = pathToSlugPrefix([ organisation.slug, quickCleanPadname(form.cleaned_data['name']) ])
            slug = publication_prefix + 'index.md'

            # Copy over publication index template
            author = PadAuthor.objects.get(user=request.user)
            group = author.group.all()[0] # Change .all()[0] to .first() ?
            
            try:
                templatePad = Pad.objects.get(display_slug=settings.PUBLICATION_TEMPLATE_PAD)
            except Pad.DoesNotExist:
                templatePad = None

            pad = createPad(slug=slug, server=group.server, group=group, templatePad=templatePad)
            formatPad(pad, title=form.cleaned_data['name'])
            # If this works add it to the normal pads too.

            # discover labels
            templateLabelsPad = discoverPad(settings.LABEL_PAD, [ organisation.slug ])
            # Copy over Labels.md and make a pad in the publication
            createPad(slug=publication_prefix + settings.LABEL_PAD, server=group.server, group=group, templatePad=templateLabelsPad)
            
            return redirect('pad-write', pad.display_slug)
    else:
        form = PublicationForm(organisation_slug=organisation.slug)

    context = {
        'form': form,
        'organisation_slug': organisation.slug
    }

    return render(request, 'going-hybrid/publication-create.html', context)