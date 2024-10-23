from django.conf import settings
from py_etherpad import EtherpadLiteClient
import urllib
import os.path
import re
from etherpadlite.models import Pad


# Natural sort a list of pads
# https://stackoverflow.com/a/11150413
def naturalSort(pads): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda pad: [convert(c) for c in re.split('([0-9]+)', pad.display_slug)] 
    return sorted(pads, key=alphanum_key)


def getApiURL (server):
    return settings.API_LOCAL_URL if settings.API_LOCAL_URL else server.apiurl


def getPadId (pad):
    return pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(settings.PAD_NAMESPACE_SEPARATOR, '_'))


def getPadBySlug (slug):
    try:
        return Pad.objects.get(display_slug=slug)
    except Pad.DoesNotExist:
        return None


def getEtherpadLiteClient(server):
    return EtherpadLiteClient(server.apikey, getApiURL(server))

# @FIXME better naming, tries to find a given padname within a path
# makes path less specific with each iteration untill a pad is found.
# a/b/c/padname → a/b/padname → a/padname → padname
def discoverPad(padname, path=[]):
  pad = getPadBySlug(pathToSlugPrefix(path) + padname)

  if pad:
    return pad
  elif len(path) > 0:
    path.pop()
    return discoverPad(padname, path=path)
  else:
    return None


"""
    Takes Pad instance as argument and return text.
    Place for a shortlived cache?
"""
def getPadText (pad):
    epclient = getEtherpadLiteClient(pad.server)
    padId = getPadId(pad)
    return epclient.getText(padId)['text']


"""
    Takes Pad instance as argument and sets the given text.
"""
def setPadText (pad, text):
    epclient = getEtherpadLiteClient(pad.server)
    padId = getPadId(pad)
    return epclient.setText(padId, text)


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


def getPadLastEdited (pad):
    epclient = getEtherpadLiteClient(pad.server)
    padId = getPadId(pad)
    return epclient.getLastEdited(padId)


"""
  .format operation. But on the text of a pad.
"""
def formatPad (pad, *args, **kwargs):
    padText = getPadText(pad)
    padText = padText.format(*args, **kwargs)
    return setPadText(pad, padText)
    

def slugToPath (slug):
    return slug.split(settings.PAD_NAMESPACE_SEPARATOR)


def pathToSlug (path):
    return settings.PAD_NAMESPACE_SEPARATOR.join(path)


def pathToSlugPrefix (path):
    if path:
        return pathToSlug(path) + settings.PAD_NAMESPACE_SEPARATOR
    else:
        return ''


def basenameFromSlug (slug):
    return slugToPath(slug)[-1]


def selectPadsByPath (path):
    if len(path) > 0:
        pads = naturalSort(list(Pad.objects.filter(display_slug__startswith=pathToSlugPrefix(path)).order_by('display_slug')))
    else:
        pads = naturalSort(list(Pad.objects.all().order_by('display_slug')))

    return pads

# Returns all root folders
# @FIXME faster implementation
def discoverFolders (path=None):
    folders = set()

    if not path:
        prefix = ''    
        pads = Pad.objects.all() 
    else:
        prefix = pathToSlugPrefix(path)
        pads = Pad.objects.filter(display_slug__startswith=prefix)

    for pad in pads:
        path = slugToPath(pad.display_slug[len(prefix):])

        if len(path) > 1:
            folders.add(path[0])

    return list(folders)


def discoverRootFolders ():
    return discoverFolders()

"""
    When pad lines have styles they are returned with a leading asterisk on text export.
    This functions strips leading asterisks if all lines start with one.
"""
def stripLeadingAsterisks (padText):
    lines = padText.split('\n')

    if all([True if line.startswith('*') or line == '' else False for line in lines]):
        return '\n'.join([line[1:] for line in lines])
    else:
        return padText
    
def quickCleanPadname (raw):
    return re.sub(r'\s+', '_', raw).strip(':')


# From easy thumbnails
def dynamic_import(import_string):
    """
    Dynamically import a module or object.
    """
    # Use rfind rather than rsplit for Python 2.3 compatibility.
    lastdot = import_string.rfind('.')
    if lastdot == -1:
        return __import__(import_string, {}, {}, [])
    module_name, attr = import_string[:lastdot], import_string[lastdot + 1:]
    parent_module = __import__(module_name, {}, {}, [attr])
    return getattr(parent_module, attr)

# Wrappers around class instantiating.
# Allowing to change them through settings.
# Would a proxy be an option?
def ethertoff_path (*args, **kwargs):
    if not hasattr(settings, 'ETHERTOFF_PATH_CLASS'):
        settings.ETHERTOFF_PATH_CLASS = 'ethertoff.models.EthertoffPath'

    return dynamic_import(settings.ETHERTOFF_PATH_CLASS)


def ethertoff_directory (*args, **kwargs):
    if not hasattr(settings, 'ETHERTOFF_DIRECTORY_CLASS'):
        settings.ETHERTOFF_DIRECTORY_CLASS = 'ethertoff.models.EthertoffDirectory'

    return dynamic_import(settings.ETHERTOFF_DIRECTORY_CLASS)


def ethertoff_pad (*args, **kwargs):
    if not hasattr(settings, 'ETHERTOFF_PAD_CLASS'):
        settings.ETHERTOFF_PAD_CLASS = 'ethertoff.models.EthertoffPad'

    return dynamic_import(settings.ETHERTOFF_PAD_CLASS)
