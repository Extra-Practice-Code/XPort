from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from ethertoff.breadcrumbs import breadcrumbs
from ethertoff.utils import stripLeadingAsterisks, ethertoff_path, formatPad, getPadText, selectPadsByPath, slugToPath, quickCleanPadname
import os.path
from etherpadlite.models import Pad, PadAuthor
from ethertoff.models import EthertoffPath
from ethertoff.views import createPad
from going_hybrid.models import EtherportOrganisation
from generator.utils import loadPublications, discoverThemeResourcePad, discoverUserPublications, getPublicationData
from generator import ALLOWED_RESOURCE_NAMES, PUBLICATION_STATE_PUBLIC, PUBLICATION_STATE_HIDDEN, PUBLICATION_STATE_UNPUBLISHED
from generator.settings import DEBUG as GENERATOR_DEBUG
from generator.management.commands.generate import generate_publication
from generator.forms import PublicationGenerationForm

from my_project.forms import PadCreateWithTemplate

# Utility function to return a theme resource
def get_theme_resource (organisation_slug, publication, resource_name, mime_type):
    resource_basename = os.path.splitext(resource_name)[0]
    publications_data = loadPublications()

    try:
        theme = publications_data[organisation_slug][publication]['visual-style']
    except KeyError:
        theme = None

    if resource_basename in ALLOWED_RESOURCE_NAMES:
        pad = discoverThemeResourcePad(organisation_slug=organisation_slug, publication=publication, resource_name=resource_name, theme=theme)

        if pad:
            text = getPadText(pad)
            text = stripLeadingAsterisks(text)

            return HttpResponse(text, content_type=mime_type)
            
        return HttpResponse("", content_type=mime_type)
    else:
        raise Http404()


# Return a css resource
def generator_css (request, organisation_slug, publication, sheet):
    return get_theme_resource(organisation_slug, publication, f'{sheet}.css', 'text/css')


# Return a javascript resource
def generator_javascript (request, organisation_slug, publication, script):
    return get_theme_resource(organisation_slug, publication, f'{script}.js', 'application/javascript')


# Move over generation logic from main project
@login_required(login_url='/accounts/login')
def generate (request):
    if request.method == 'POST':
        form = PublicationGenerationForm(request.POST)

        if form.is_valid():
            publication_slug = form.cleaned_data['publication_slug']
            organisation_slug = form.cleaned_data['organisation_slug']
            mode = form.cleaned_data['mode']
            next_state = form.cleaned_data['next_state']
            organisation = get_object_or_404(EtherportOrganisation, slug=organisation_slug, members__id=request.user.id)
            result = generate_publication(organisation, publication_slug, mode, next_state)
            
        else:
            print('Form not valid?')
            print(form.errors)

        # Add organisation URL.
        return render(request, "generator/result.html", { 'result': result, 'publication_manage_url': reverse('manage', args=[settings.PAD_NAMESPACE_SEPARATOR.join([organisation_slug, publication_slug])]) })
    else:
        return redirect('generator-list-publications')


# List publications, group by organisation linked to the account
# per publication show:
#   state
#   mode
#   actions: generate, hide | show
@login_required(login_url='/accounts/login')
def list_publications (request):
    # Render template
    return render(request, "etherport/list-publications.html", {
        'user_organisations': discoverUserPublications(user=request.user),
        'publication_states': {
            'public': PUBLICATION_STATE_PUBLIC,
            'hidden': PUBLICATION_STATE_HIDDEN,
            'unpublished': PUBLICATION_STATE_UNPUBLISHED
        }
    })

# @FIXME, move views into going hybrid and rename to etherport?
@login_required(login_url='/accounts/login')
def manage(request, directory=None):
    if not directory:
        return redirect('generator-list-publications')

    organisation = directory.path[0]#get_object_or_404(EtherportOrganisation, slug=directory.path[0].slug, members__id=request.user.id)
    
    # prefix = pathToSlugPrefix(path)

    # pads = Pad.objects.filter(display_slug__startswith=prefix).order_by(Lower('display_slug'))
    
    dir_list = []
    seen_dirs = []

    prefix = directory.toPrefix()

    # Loop through pads. If it is within a subfolder only show first folder.
    for pad in directory.pads:
        relativePath = pad.display_slug[len(prefix):]

        if settings.PAD_NAMESPACE_SEPARATOR in relativePath:
            # Pad has a namespace separator in its display slug. Therefor is a pad
            # in a subfolder. Add a directory entry and do not add the pad.
            key = relativePath.split(settings.PAD_NAMESPACE_SEPARATOR, 1)[0]
            if key not in seen_dirs:
                dir_list.append((key, 'directory', None, prefix + key))
                seen_dirs.append(key)
        else:
            dir_list.append((relativePath, 'pad', pad, pad.display_slug))
      
    return render(request, "etherport/manage-tree.html", {
        'organisation': organisation,
        'dir_list': dir_list,
        'currentPath': prefix,
        'directory': directory,
        'crumbs': breadcrumbs(request, directory.path, directory),
        'has_visual_styles': 'Visual_Styles' in seen_dirs,
        'PAD_OPEN_MODE': settings.TREE_PAD_OPEN_MODE
    })




# # Adjusted version of pad renaming which takes organisation 
# # and publication structure into account
# @login_required(login_url='/etherpad')
# def padRename(request, pk):
#     pad = get_object_or_404(Pad, pk=pk)
    
#     if request.method == 'POST':
#         form = ethertoffForms.RenamePadForm(request.POST)
#         if form.is_valid():
#             folder = quickCleanPadname(form.cleaned_data['new_folder'])
#             name = quickCleanPadname(form.cleaned_data['new_name'])
#             slug = folder + settings.PAD_NAMESPACE_SEPARATOR + name
#             renamePad(pad, slug)

#             if folder:
#                 # path = path.replace(settings.PAD_NAMESPACE_SEPARATOR, '/')
#                 return redirect('manage', path_string=folder)
#             else:
#                 return redirect('manage')

#     else:
#         # Get folder and name for this display slug
#         parts = pad.display_slug.rsplit(settings.PAD_NAMESPACE_SEPARATOR, 1)

#         if len(parts) > 1:
#             folder, name = parts
#         else:
#             folder = ''
#             name = parts[0]

#         form = ethertoffForms.RenamePadForm({
#             'pk': pad.pk,
#             'old_folder': folder,
#             'old_name': name,
#             'new_folder': folder,
#             'new_name': name,
#         })

#     context = {
#         'form': form,
#         'pk': pad.pk,
#         'title': _('Rename pad {}').format(str(pad))
#     }

#     context.update(csrf(request))

#     return render(
#         request,
#         'pad-rename.html',
#         context
#     )



@login_required(login_url='/accounts/login')
def padCreate(request, directory):
    """
    Create a pad
    """    
    # if len(path) < 2:
    #     # Error handling
    #     return
    
    organisation = get_object_or_404(EtherportOrganisation, slug=directory.path[0].slug, members__id=request.user.id)
    publication = getPublicationData(organisation.slug, directory.path[1].slug if len(directory.path) > 2 else directory.slug)

    templateChoices = [('none', "No template")] + [
        (pad.name, '>'.join(slugToPath(pad.display_slug)[2:])) for pad in selectPadsByPath([ organisation.slug, 'Templates' ])
    ]

    # normally the ‘pads’ context processor should have made sure that these objects exist:
    author = PadAuthor.objects.get(user=request.user)
    group = author.group.all()[0]
    
    if request.method == 'POST':  # Process the form
        form = PadCreateWithTemplate(request.POST)
        form.fields['template'].choices = templateChoices
        if form.is_valid():
            slug = directory.toPrefix()
            folder = quickCleanPadname(form.cleaned_data['folder'])
            if folder and folder != '':
                slug += folder +  settings.PAD_NAMESPACE_SEPARATOR 

            name = quickCleanPadname(form.cleaned_data['name'])
            slug += name

            templatePad = None

            if form.cleaned_data['template'] != 'none':
                try:
                    templatePad = Pad.objects.get(name=form.cleaned_data['template'])
                except Pad.DoesNotExist:
                    pass

            pad = createPad(slug=slug, server=group.server, group=group, templatePad=templatePad)

            if templatePad:
                formatPad(pad, title=form.cleaned_data['name'])

            if pad:
                return redirect('pad-write', pad.display_slug)
    else: 
        # No form to process so create a fresh one
        # prefix should contain the name of the folder
        form = PadCreateWithTemplate({
            'group': group.groupID,
            # @FIXME
            'folder': ethertoff_path()(directory.path[2:]).toSlug(),
            'name': ''
        })
        form.fields['template'].choices = templateChoices
        
    con = {
        'form': form,
        'pk': group.pk,
        'slug': organisation.slug,
        'directory': directory,
        'title': _('Create pad in: {}').format(' > '.join(map(str, directory.path)))
    }
    # con.update(csrf(request))
    return render(
        request,
        'etherport/pad-create.html',
        con,
    )




