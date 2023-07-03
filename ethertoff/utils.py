from django.conf import settings
from py_etherpad import EtherpadLiteClient
import urllib
import os.path


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
