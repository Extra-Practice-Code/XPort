from django.conf import settings
from py_etherpad import EtherpadLiteClient
import urllib
import os.path
import re
from etherpadlite.models import Pad

# Natural sort a list of pads
# https://stackoverflow.com/a/11150413
def natural_sort(pads): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda pad: [convert(c) for c in re.split('([0-9]+)', pad.display_slug)] 
    return sorted(pads, key=alphanum_key)


def getApiURL (server):
    return settings.API_LOCAL_URL if settings.API_LOCAL_URL else server.apiurl


def getPadId (pad):
    return pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(settings.PAD_NAMESPACE_SEPARATOR, '_'))


def getEtherpadLiteClient(server):
    return EtherpadLiteClient(server.apikey, getApiURL(server))


"""
    Takes Pad instance as argument and return text.
    Place for a shortlived cache?
"""
def getPadText (pad):
    epclient = getEtherpadLiteClient(pad.server)
    padId = getPadId(pad)
    return epclient.getText(padId)['text']


def getPadMarkdown (pad):
    padId = getPadId(pad)
    try:
        url = os.path.join(pad.server.url, 'p', padId, 'export/markdown')
        response = urllib.request.urlopen(url)
        markdown = response.read().decode('utf-8')
    except urllib.error.HTTPError:
        raise
    return markdown


def getPadHtml (pad):
    epclient = getEtherpadLiteClient(pad.server)
    padId = getPadId(pad)
    return epclient.getHtml(padId)['html']


def pathToSlugPrefix (path):
    return settings.PAD_NAMESPACE_SEPARATOR.join(path) + settings.PAD_NAMESPACE_SEPARATOR


def selectPadsByPath (path):
    if len(path) > 0:
        pads = natural_sort(list(Pad.objects.filter(display_slug__startswith=pathToSlugPrefix(path)).order_by('display_slug')))
    else:
        pads = natural_sort(list(Pad.objects.all().order_by('display_slug')))

    return pads