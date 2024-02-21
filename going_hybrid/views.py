from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from ethertoff.models import EtherportOrganisation
from ethertoff.views import createPad
from etherpadlite.models import Pad, PadAuthor
from going_hybrid.forms import PublicationForm
from py_etherpad import EtherpadLiteClient
from ethertoff.utils import pathToSlugPrefix, quickCleanPadname

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
          
          publication_name = quickCleanPadname(form.cleaned_data['name'])
          slug_prefix = pathToSlugPrefix([ organisation.slug, publication_name ])
          slug = slug_prefix + 'index.md'

          # Copy over publication index template
          author = PadAuthor.objects.get(user=request.user)
          group = author.group.all()[0] 
          pad = createPad(slug=slug, server=group.server, group=group)

          try:
              templatePad = Pad.objects.get(display_slug=settings.PUBLICATION_TEMPLATE_PAD)
              epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)
              epclient.copyPadWithoutHistory(templatePad.padid, pad.padid, True)

          except Pad.DoesNotExist:
              pass
          
          return redirect('pad-write', pad.display_slug)
    else:
        form = PublicationForm(organisation_slug=organisation.slug)

    context = {
         'form': form,
         'organisation_slug': organisation.slug
    }

    return render(request, 'going-hybrid/publication-create.html', context)