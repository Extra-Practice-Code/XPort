from django.http import Http404, HttpResponse
from ethertoff.utils import stripLeadingAsterisks, pathToSlug, getPadText
import os.path
from generator.utils import loadPublications, discoverThemeResourcePad

ALLOWED_RESOURCE_NAMES = [ 'screen', 'print', 'common' ]

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
        

def generator_css (request, organisation_slug, publication, sheet):
    return get_theme_resource(organisation_slug, publication, f'{sheet}.css', 'text/css')
      

def generator_javascript (request, organisation_slug, publication, script):
    return get_theme_resource(organisation_slug, publication, f'{script}.js', 'application/javascript')


