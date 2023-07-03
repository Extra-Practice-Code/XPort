# -*- coding: utf-8 -*-

# Python imports
import datetime
import time
import urllib
from urllib.parse import urlparse
from html.parser import HTMLParser
import json
import re
import os

# PyPi imports

import markdown
from markdown.extensions.toc import TocExtension
from generator.markdown_inline_reference import InlineReferenceExtension
# from mdx_semanticdata import SemanticDataExtension
from py_etherpad import EtherpadLiteClient
import dateutil.parser
import pytz

# Framework imports
from django.shortcuts import render, get_object_or_404, redirect

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError
from django.conf import settings
from django.contrib.staticfiles import finders

# Django Apps import

from etherpadlite.models import Pad, PadAuthor
from etherpadlite import forms
from etherpadlite import config

from ethertoff.management.commands.index import snif
from ethertoff.templatetags.wikify import wikifyPath, ensureTrailingSlash

# Generator commands
from generator.management.commands.generate import generate as generateStatic
from tags.utils import index_tags as indexTags
from generator.collection import modelFor

from . import forms as ethertoffForms

from ethertoff.forms import RenameFolderForm, RenamePadForm
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from django.views.decorators.clickjacking import xframe_options_exempt

from tags.utils import load_tags

from ethertoff.utils import getApiURL, getPadId, getEtherpadLiteClient, getPadText, getPadMarkdown

# By default, the homepage is the pad called ‘start’ (props to DokuWiki!)
try:
    HOME_PAD = settings.HOME_PAD
except ImportError:
    HOME_PAD = 'About.md'
try:
    BACKUP_DIR = settings.BACKUP_DIR
except ImportError:
    BACKUP_DIR = None

"""
Set up an HTMLParser for the sole purpose of unescaping
Etherpad’s HTML entities.
cf http://fredericiana.com/2010/10/08/decoding-html-entities-to-text-in-python/
"""

try:
    h = HTMLParser()
    unescape = h.unescape
except AttributeError:
    import html
    unescape = html.unescape

"""
Create a regex for our include template tag
"""
include_regex = re.compile("{%\s?include\s?\"([\w._-]+)\"\s?%}")




# Perhaps move to the model?
def makePadPublic (pad, n=0):
    if not pad.is_public:
        epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)
        tail = '' if n == 0 else '-{}'.format(n)
        publicid = pad.name+tail

        try:
            res = epclient.sendClientsMessage(pad.padid, "Please continue editing in the public version of this pad")
            print(res)
            res = epclient.copyPad(pad.padid, publicid)
            pad.is_public = True
            pad.publicpadid = publicid
            pad.save()

            return pad
        
        except ValueError:
            return makePadPublic(pad, n+1)

def makePadPrivate(pad):
    if pad.is_public:
        epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)
        res = epclient.movePad(pad.publicpadid, pad.padid, force=True)

        pad.is_public = False
        pad.publicpadid = ''
        pad.save()
        return pad

# Filter out forbidden
def filterPadSlug(slug):
    # Replace spaces by '_'
    slug = re.sub(r'\s', '_', slug)
    # Replace forbidden characters
    slug = re.sub(r'[/]', '', slug)

    return slug 

def ensureExtension(slug):
    name, ext = os.path.splitext(slug)

    if settings.PAD_FORCE_EXTENSION:
        if ext.lower() not in settings.PAD_ALLOWED_EXTENSIONS:
            ext = settings.PAD_DEFAULT_EXTENSION

        return '{}{}'.format(name, ext.lower())

    return '{}{}'.format(name, ext.lower()) 

def insertNumberBeforeExtension (name, n=0):
    if n > 0:
        name, ext = os.path.splitext(name)
        name = '{}-{}'.format(name, n)

        return '{}{}'.format(name, ext)
    else:
        return name

def treatPadName(slug, n):
    return insertNumberBeforeExtension(
        ensureExtension(
            filterPadSlug(slug)), n)

def createPad (slug, server, group, n=0):
    if n < 25:
        try:
            safe_slug = treatPadName(slug, n)
            pad = Pad(
                name=slugify(safe_slug)[:42], # This is the slug internally used by etherpad
                display_slug=safe_slug, # This is the slug we get to change afterwards
                server=group.server,
                group=group
            )

            pad.save()
            return pad
        except ValueError:
            # Pad already exists on the server
            return createPad(slug=slug, server=server, group=group, n=n+1)
        except IntegrityError:
            # Pad existed in the database, but not on the server
            # delete the created pad
            pad.Destroy()
            return createPad(slug=slug, server=server, group=group, n=n+1)

    return False

# Move as a property to the model ?
def getFolderName (slug):
    if settings.PAD_NAMESPACE_SEPARATOR in slug:
        return slug.rsplit(settings.PAD_NAMESPACE_SEPARATOR, 1)[0]
    else:
        return None

@login_required(login_url='/accounts/login')
def padCreate(request, prefix=''):
    """
    Create a pad
    """    
    
    # normally the ‘pads’ context processor should have made sure that these objects exist:
    author = PadAuthor.objects.get(user=request.user)
    group = author.group.all()[0]
    
    if request.method == 'POST':  # Process the form
        form = forms.PadCreate(request.POST)
        if form.is_valid():
            slug = re.sub(r'\s+', '_', form.cleaned_data['name'])
            slug = slug.strip(":")  # avoids leading and trailing "::"
            pad = createPad(slug=slug, server=group.server, group=group)

            if pad:
                template = None

                # Make a template for the seleced datatype
                if form.cleaned_data['template'] != 'none':
                    model = modelFor(form.cleaned_data['template'])(1)
                    template = '\n'.join(['{}: {}'.format(fieldName, field.value if field.value else '') for fieldName, field in model.fields.items()])

                    epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)
                    epclient.setText(pad.padid, template)

                return HttpResponseRedirect(reverse('pad-write', args=(pad.display_slug,) ))
    else: 
        # No form to process so create a fresh one
        # prefix should contain the name of the folder
        form = forms.PadCreate({'group': group.groupID, 'name': wikifyPath(ensureTrailingSlash(prefix) if prefix else '')})

    con = {
        'form': form,
        'pk': group.pk,
        'title': _('Create pad in %(grp)s') % {'grp': group}
    }
    con.update(csrf(request))
    return render(
        request,
        'pad-create.html',
        con,
    )


@login_required(login_url='/etherpad')
def padDelete(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(Pad, pk=pk)

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            pad.delete()
        return HttpResponseRedirect('/manage/')

    con = {
        'action': reverse('pad-delete', kwargs={'pk': pk}),
        'question': _('Really delete the pad {}?'.format(str(pad))),
        'title': _('Deleting {}'.format(str(pad))),
        'label': _('Delete')
    }
    con.update(csrf(request))
    return render(
        request,
        'pads/confirm.html',
        con
    )


"""
    Renames a pad to the given slug.
    If the desired name already exists a number is added before the extension.
    name.md → name-1.md
"""
def renamePad(pad, slug, n=0):
    pad.display_slug = treatPadName(slug, n)
    
    while n < settings.MAX_PAD_SAVE_TRIES:
        try:
            return pad.save()
        except IntegrityError:
            return renamePad(pad, slug, n+1)

    raise IntegrityError

@login_required(login_url='/etherpad')
def padRename(request, pk):
    pad = get_object_or_404(Pad, pk=pk)

    if request.method == 'POST':
        form = ethertoffForms.RenamePadForm(request.POST)
        if form.is_valid():
            slug = re.sub(r'\s+', '_', form.cleaned_data['new_name'])
            slug = slug.strip(":")  # avoids leading and trailing "::"
            renamePad(pad, slug)

            path = getFolderName(pad.display_slug)

            if path:
                path = path.replace(settings.PAD_NAMESPACE_SEPARATOR, '/')
                return redirect('manage', path=path)
            else:
                return redirect('manage')

    else:
        print(pad.pk)
        form = ethertoffForms.RenamePadForm({
            'pk': pad.pk,
            'old_name': pad.display_slug,
            'new_name': pad.display_slug,
        })

    context = {
        'form': form,
        'pk': pad.pk,
        'title': _('Rename pad {}').format(str(pad))
    }

    context.update(csrf(request))

    return render(
        request,
        'pad-rename.html',
        context
    )

class RenamePadView(FormView):
    template_name = 'pad-rename.html'
    form_class = RenamePadForm

class RenameFolderView(FormView):
    template_name = 'folder-rename.html'
    form_class = RenameFolderForm
    success_url = reverse_lazy('manage')

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        old_name = self.kwargs.get("prefix", "") 
        old_name = old_name.replace('/', settings.PAD_NAMESPACE_SEPARATOR)
        old_name = old_name.strip(":")  # avoids leading and trailing "::"
        self.initial.update({"old_name": old_name})
        self.initial.update({"new_name": old_name})
        return super().get_initial()


    def form_valid(self, form):
        old_name = form.cleaned_data.get('old_name')
        new_name = form.cleaned_data.get('new_name')
        for pad in Pad.objects.filter(display_slug__startswith=old_name):
            current_display_slug = pad.display_slug
            new_display_slug = new_name + current_display_slug[len(old_name):]
            # Use renamePad function to deal with name conflicts
            renamePad(pad, new_display_slug)
            # pad.display_slug = new_display_slug
            # pad.save()
        return super().form_valid(form)

@login_required(login_url='/etherpad')
def padPublic(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(Pad, pk=pk)

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            makePadPublic(pad)
        return HttpResponseRedirect('/manage/')

    con = {
        'action': reverse('pad-public', kwargs={'pk': pk}),
        'question': _('Really make {} public?'.format(str(pad))),
        'title': _('Making {} public'.format(str(pad))),
        'label': _('Make public')
    }
    con.update(csrf(request))
    return render(
        request,
        'pads/confirm.html',
        con
    )


@login_required(login_url='/etherpad')
def padPrivate(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(Pad, pk=pk)

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            makePadPrivate(pad)
        return HttpResponseRedirect('/manage/')

    con = {
        'action': reverse('pad-private', kwargs={'pk': pk}),
        'question': _('Really make {} private?'.format(str(pad))),
        'title': _('Making {} private'.format(str(pad))),
        'label': _('Make private')
    }
    con.update(csrf(request))
    return render(
        request,
        'pads/confirm.html',
        con
    )

def pad(request, pk=None, slug=None, mode=None):
    if slug:
        pad = get_object_or_404(Pad, display_slug=slug)
    else:
        pad = get_object_or_404(Pad, pk=pk)

    if pad.is_public:
        return pad_write_public(request, pad)
    else:
        return pad_write(request, pad)

def pad_write_public(request, pad): # pad_write
    padLink = pad.server.url + 'p/' + pad.publicpadid
    server = urlparse(pad.server.url)
    
    path = pad.display_slug.split(settings.PAD_NAMESPACE_SEPARATOR)
    crumbs = [(path[i], path[:i+1]) for i in range(len(path))]

    if request.user.is_authenticated:
        author = PadAuthor.objects.get(user=request.user)
        uname = str(author.user)
    else:
        uname = None

    # Set up the response
    return render(
        request,
        'pad-public.html',
        {
            'pad': pad,
            'link': padLink,
            'server': server,
            'error': False,
            'mode' : 'write-public',
            'uname': uname,
            'crumbs': crumbs
        },
    )

@login_required(login_url='/accounts/login')
def pad_write(request, pad):
    # pad_write
    
    """
     Create and session and display an embedded pad
    """
    padLink = pad.server.url + 'p/' + pad.group.groupID + '$' + \
        urllib.parse.quote(pad.name)
    server = urlparse(pad.server.url)
    author = PadAuthor.objects.get(user=request.user)

    path = pad.display_slug.split(settings.PAD_NAMESPACE_SEPARATOR)
    crumbs = [(path[i], path[:i+1]) for i in range(len(path))]

    if author not in pad.group.authors.all():
        response = render(
            request,
            'pad.html',
            {
                'pad': pad,
                'link': padLink,
                'server': server,
                'uname': "{}".format(author.user),
                'error': _('You are not allowed to view or edit this pad')
            },
            context_instance=RequestContext(request)
        )
        return response

    # Create the session on the etherpad-lite side
    expires = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=config.SESSION_LENGTH
    )
    epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)

    # Try to use existing session as to allow editing multiple pads at once
    makeNewSessionID = False

    try:
        if not 'sessionID' in request.COOKIES:
            makeNewSessionID = True

            result = epclient.createSession(
                pad.group.groupID,
                author.authorID,
                time.mktime(expires.timetuple()).__str__()
            )
    except Exception as e:
        response =  render(
            request,
            'pad.html',
            {
                'pad': pad,
                'link': padLink,
                'server': server,
                'uname': "{}".format(author.user),
                'error': _('etherpad-lite session request returned:') +
                ' "' + e.reason if isinstance(e, UnicodeError) else str(e) + '"'
            }
        )
        return response

    # Set up the response
    response = render(
        request,
        'pad.html',
        {
            'pad': pad,
            'link': padLink,
            'server': server,
            'uname': "{}".format(author.user),
            'error': False,
            'mode' : 'write',
            'crumbs': crumbs,
            'tags': load_tags()
        },
    )

    if makeNewSessionID:
        # Delete the existing session first
        if ('padSessionID' in request.COOKIES):
            if 'sessionID' in request.COOKIES.keys():
                try:
                    epclient.deleteSession(request.COOKIES['sessionID'])
                except ValueError:
                    response.delete_cookie('sessionID', server.hostname)
            response.delete_cookie('padSessionID')

        # Set the new session cookie for both the server and the local site
        response.set_cookie(
            'sessionID',
            value=result['sessionID'],
            expires=expires,
            domain=server.hostname,
            httponly=False
        )
        response.set_cookie(
            'padSessionID',
            value=result['sessionID'],
            expires=expires,
            httponly=False
        )
        
    return response

# @FIXME either implement or remove?
# Archiving command
def xhtml(request, slug):
    return pad_read(request, "r", slug + '.md')


@xframe_options_exempt
def pad_read(request, mode="r", slug=None):
    """Read only pad
    """
    
    # FIND OUT WHERE WE ARE,
    # then get previous and next
    try:
        articles = json.load(open(os.path.join(BACKUP_DIR, 'index.json')))
    except IOError:
        articles = []
    
    # FIXME: construct url based on settings?
    # SITE = get_current_site(request)
    #href = "http://%s" % SITE.domain + request.path
    
    href = request.path

    prev = None
    next = None
    for i, article in enumerate(articles):
        if article['href'] == href:
            if i != 0:        # The first is the most recent article, there is no newer
                next = articles[i-1]
            if i != len(articles) - 1:
                prev = articles[i+1]

    # Initialize some needed values
    pad = get_object_or_404(Pad, display_slug=slug)

    padID = pad.publicpadid if pad.is_public else pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(settings.PAD_NAMESPACE_SEPARATOR, '_'))
    epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)

    # Etherpad gives us authorIDs in the form ['a.5hBzfuNdqX6gQhgz', 'a.tLCCEnNVJ5aXkyVI']
    # We link them to the Django users DjangoEtherpadLite created for us
    authorIDs = epclient.listAuthorsOfPad(padID)['authorIDs']
    authors = PadAuthor.objects.filter(authorID__in=authorIDs)

    authorship_authors = []
    for author in authors:
        authorship_authors.append({ 'name'  : author.user.first_name if author.user.first_name else author.user.username,
                                    'class' : 'author' + author.authorID.replace('.','_') })
    authorship_authors_json = json.dumps(authorship_authors, indent=2)

    name, extension = os.path.splitext(slug)

    meta = {}

    if not extension:
        # Etherpad has a quasi-WYSIWYG functionality.
        # Though is not alwasy dependable
        text = epclient.getHtml(padID)['html']
        # Quick and dirty hack to allow HTML in pads
        text = unescape(text)
    else:
        # If a pad is named something.css, something.html, something.md etcetera,
        # we don’t want Etherpads automatically generated HTML, we want plain text.
        # text = epclient.getText(padID)['text']
        text = getPadMarkdown(pad)
        if extension in ['.md', '.markdown']:
            md = markdown.Markdown(**settings.MARKDOWN_SETTINGS)
            text = md.convert(text)
            try:
                meta = md.Meta
            except AttributeError:   # Edge-case: this happens when the pad is completely empty
                meta = None
    
    # Convert the {% include %} tags into a form easily digestible by jquery
    # {% include "example.html" %} -> <a id="include-example.html" class="include" href="/r/include-example.html">include-example.html</a>
    def ret(matchobj):
        return '<a id="include-%s" class="include pad-%s" href="%s">%s</a>' % (slugify(matchobj.group(1)), slugify(matchobj.group(1)), reverse('pad-read', args=("r", matchobj.group(1)) ), matchobj.group(1))
    
    text = include_regex.sub(ret, text)
    
    
    # Create namespaces from the url of the pad
    # 'pedagogy::methodology' -> ['pedagogy', 'methodology']
    namespaces = [p.rstrip('-') for p in pad.display_slug.split(settings.PAD_NAMESPACE_SEPARATOR)]

    meta_list = []

    # One needs to set the ‘Static’ metadata to ‘Public’ for the page to be accessible to outside visitors
    if not meta or not 'status' in meta or not meta['status'][0] or not meta['status'][0].lower() in ['public']:
        if not request.user.is_authenticated:
            pass #raise PermissionDenied
    
    if meta and len(meta.keys()) > 0:
        
        # The human-readable date is parsed so we can sort all the articles
        if 'date' in meta:
            meta['date_iso'] = []
            meta['date_parsed'] = []
            for date in meta['date']:
                try:
                    date_parsed = dateutil.parser.parse(date)
                    # If there is no timezone we assume it is in Brussels:
                    if not date_parsed.tzinfo:
                        date_parsed = pytz.timezone('Europe/Brussels').localize(date_parsed)
                    meta['date_parsed'].append(date_parsed)
                    meta['date_iso'].append( date_parsed.isoformat() )
                except ValueError:
                    continue

        meta_list = list(meta.items())


    tpl_params = { 'pad'                : pad,
                   'meta'               : meta,      # to access by hash, like meta.author
                   'meta_list'          : meta_list, # to access all meta info in a (key, value) list
                   'text'               : text,
                   'prev_page'          : prev,
                   'next_page'          : next,
                   'mode'               : mode,
                   'namespaces'         : namespaces,
                   'authorship_authors_json' : authorship_authors_json,
                   'authors'            : authors }

    if not request.user.is_authenticated:
        request.session.set_test_cookie()
        tpl_params['next'] = reverse('pad-write', args=(slug,) )

    if mode == "r":
        return render(request, "pad-read.html", tpl_params)
    elif mode == "s":
        return render(request, "pad-slide.html", tpl_params)
    elif mode == "p":
        return render(request, "pad-print.html", tpl_params)



def home(request):
    return all(request)
    
    try:
        articles = json.load(open(os.path.join(BACKUP_DIR, 'index.json')))
    except IOError: # If there is no index.json generated, we go to the defined homepage
        try:
            Pad.objects.get(display_slug=HOME_PAD)
            return pad_read(request, slug=HOME_PAD)
        except Pad.DoesNotExist: # If there is no homepage defined we go to the login:
            return HttpResponseRedirect(reverse('login'))
    
    sort = 'date'
    if 'sort' in request.GET:
        sort = request.GET['sort']

    hash = {}
    for article in articles:
        if sort in article:
            if isinstance(article[sort], str):
                subject = article[sort]
                if not subject in hash:
                    hash[subject] = [article]
                else:
                    hash[subject].append(article)
            else:
                for subject in article[sort]:
                    if not subject in hash:
                        hash[subject] = [article]
                    else:
                        hash[subject].append(article)
    tpl_articles = []
    for subject in sorted(hash.keys()):
        # Add the articles sorted by date ascending:
        tpl_articles.append({
            'key' : subject,
            'values': sorted(hash[subject], key=lambda a: a['date'] if 'date' in a else 0)
        })

    tpl_params = { 'articles': tpl_articles,
                   'sort': sort }
    return render(request, "home.html", tpl_params)

@login_required(login_url='/accounts/login')
def publish(request):
    tpl_params = {}
    if request.method == 'POST':
        tpl_params['published'] = True
        tpl_params['message'] = snif()
    else:
        tpl_params['published'] = False
        tpl_params['message'] = ""
    return render(request, "publish.html", tpl_params)

@login_required(login_url='/accounts/login')
def generate(request):
    tpl_params = {}
    if request.method == 'POST':
        tpl_params['generated'] = True
        tpl_params['message'] = generateStatic()
    else:
        tpl_params['generate'] = False
        tpl_params['message'] = ""
    return render(request, "generate.html", tpl_params)


@login_required(login_url='/accounts/login')
def index_tags (request):
    tpl_params = {}
    if request.method == 'POST':
        tpl_params['indexed'] = True
        tpl_params['tags'] = indexTags()
    else:
        tpl_params['indexed'] = False
        tpl_params['tags'] = []
    return render(request, "index_tags.html", tpl_params)


@login_required(login_url='/accounts/login')
def manage(request, path=[]):
    prefix = ''

    if len(path) > 0:
        path = path.split('/')
        prefix = settings.PAD_NAMESPACE_SEPARATOR.join(path) + settings.PAD_NAMESPACE_SEPARATOR
        pads = Pad.objects.filter(display_slug__startswith=prefix).order_by('name')
    else:
        pads = Pad.objects.all().order_by('name')

    dir_list = []
    seen_dirs = []

    # Loop through pads. If it is within a subfolder only show first folder.
    for pad in pads:
        relativePath = pad.display_slug[len(prefix):]

        if settings.PAD_NAMESPACE_SEPARATOR in relativePath:
            key = relativePath.split(settings.PAD_NAMESPACE_SEPARATOR, 1)[0]
            if key not in seen_dirs:
                dir_list.append((key, 'directory', None))
                seen_dirs.append(key)
        else:
            key = relativePath
            dir_list.append((key, 'pad', pad))
            

    crumbs = [(path[i], path[:i+1]) for i in range(len(path))]

    return render(request, "manage-tree.html", {
        'dir_list': dir_list,
        'currentPath': path,
        'crumbs': crumbs,
        'PAD_OPEN_MODE': settings.TREE_PAD_OPEN_MODE
    })
    
def all(request):
    if request.user.is_authenticated:
        return manage(request)
    else:
        return all_public(request)

def all_public(request):
    # On this install do not show public pads
    publicpads = [] # Pad.objects.filter(is_public=True)
    return render(request, "all-public.html", { 'publicpads': publicpads })

@login_required(login_url='/accounts/login')
def all_private(request):
    return render(request, "all.html")

def padOrFallbackPath(request, slug, fallbackPath, mimeType):
    try:
        pad = Pad.objects.get(display_slug=slug)
        padID = pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace(settings.PAD_NAMESPACE_SEPARATOR, '_'))
        epclient = EtherpadLiteClient(pad.server.apikey, settings.API_LOCAL_URL if settings.API_LOCAL_URL else pad.server.apiurl)
        return HttpResponse(epclient.getText(padID)['text'], content_type=mimeType)
    except:
        # If there is no pad called "css", loads a default css file
        path = finders.find(fallbackPath)
        f = open(path, 'r')
        contents = f.read()
        f.close()
        return HttpResponse(contents, content_type=mimeType)

def css(request):
    return padOrFallbackPath(request, 'screen.css', 'css/screen.css', 'text/css')

def cssprint(request):
    return padOrFallbackPath(request, 'laser.css', 'css/laser.css', 'text/css')

def offsetprint(request):
    return padOrFallbackPath(request, 'offset.css', 'css/offset.css', 'text/css')

def css_slide(request):
    return padOrFallbackPath(request, 'slidy.css', 'css/slidy.css', 'text/css')