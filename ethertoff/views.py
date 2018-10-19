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
from py_etherpad import EtherpadLiteClient
import dateutil.parser
import pytz

# Framework imports
from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.template.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError
from django.core.paginator import Paginator

# Django Apps import

from etherpadlite.models import *
from etherpadlite import forms
from etherpadlite import config
from django.contrib.sites.shortcuts import get_current_site

from ethertoff.management.commands.index import snif
from ethertoff.templatetags.wikify import wikifyPath, ensureTrailingSlash

# By default, the homepage is the pad called ‘start’ (props to DokuWiki!)
try:
    from ethertoff.settings import HOME_PAD
except ImportError:
    HOME_PAD = 'About.md'
try:
    from ethertoff.settings import BACKUP_DIR
except ImportError:
    BACKUP_DIR = None

from ethertoff.settings import PAD_FORCE_EXTENSION, PAD_ALLOWED_EXTENSIONS, PAD_DEFAULT_EXTENSION, PADS_PER_PAGE, PAD_NAMESPACE_SEPARATOR

"""
Set up an HTMLParser for the sole purpose of unescaping
Etherpad’s HTML entities.
cf http://fredericiana.com/2010/10/08/decoding-html-entities-to-text-in-python/
"""

h = HTMLParser()
unescape = h.unescape

"""
Create a regex for our include template tag
"""
include_regex = re.compile("{%\s?include\s?\"([\w._-]+)\"\s?%}")

def makeLeaf ():
    return { 'folders': {}, 'pads': [] }

def insertAt (path=[], tree=[], pad=''):
    if len(path) > 1:
        key = path.pop(0)
        if not key in tree['folders']:
            tree['folders'][key] = makeLeaf()

        tree['folders'][key] = insertAt(path, tree['folders'][key], pad)
    else:
        tree['pads'].append(pad)

    return tree

def insertPad (pad, tree):
    if PAD_NAMESPACE_SEPARATOR in pad.display_slug:
        path = pad.display_slug.split(PAD_NAMESPACE_SEPARATOR)
    else:
        path = []
    
    return insertAt(path, tree, pad)
    

# FIXME: better name
def treatPadName (name, n=0):
    name, ext = os.path.splitext(name)

    if n > 0:
        name = '{}-{}'.format(name, n)

    if PAD_FORCE_EXTENSION:
        if ext not in PAD_ALLOWED_EXTENSIONS:
            ext = PAD_DEFAULT_EXTENSION

        name = '{}{}'.format(name, ext)
    
    return name

def createPad (slug, server, group, n=0):
    if n < 25:
        try:
            safe_slug = treatPadName(slug, n)
            pad = Pad(
                name=slugify(safe_slug)[:42], # This is the slug internally used by etherpad
                display_slug=safe_slug, # This is the slug we get to change afterwards
                display_name=safe_slug,     # this is just for backwards compatibility
                server=group.server,
                group=group
            )

            pad.save()
            return pad
        except IntegrityError:
            return createPad(slug=slug, server=server, group=group, n=n+1)

    return False

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
            pad = createPad(slug=slug, server=group.server, group=group)

            return HttpResponseRedirect(reverse('pad-write', args=(pad.display_slug,) ))
    else:  # No form to process so create a fresh one
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
    }
    con.update(csrf(request))
    return render(
        request,
        'pads/confirm.html',
        con
    )


@login_required(login_url='/accounts/login')
def pad(request, pk=None, slug=None): # pad_write
    """
     Create and session and display an embedded pad
    """

    # Initialize some needed values
    if slug:
        pad = get_object_or_404(Pad, display_slug=slug)
    else:
        pad = get_object_or_404(Pad, pk=pk)
    padLink = pad.server.url + 'p/' + pad.group.groupID + '$' + \
        urllib.parse.quote(pad.name)
    server = urlparse(pad.server.url)
    author = PadAuthor.objects.get(user=request.user)

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
    epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)

    # Try to use existing session as to allow editing multiple pads at once
    newSessionID = False

    try:
        if not 'sessionID' in request.COOKIES:
            newSessionID = True

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
            'mode' : 'write'
        },
    )

    if newSessionID:
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

def xhtml(request, slug):
    return pad_read(request, "r", slug + '.md')

def pad_read(request, mode="r", slug=None):
    """Read only pad
    """
    
    # FIND OUT WHERE WE ARE,
    # then get previous and next
    try:
        articles = json.load(open(os.path.join(BACKUP_DIR, 'index.json')))
    except IOError:
        articles = []
    
    SITE = get_current_site(request)
    # FIXME: construct url based on settings?
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

    padID = pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace('::', '_'))
    epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)

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
        text = epclient.getText(padID)['text']
        if extension in ['.md', '.markdown']:
            md = markdown.Markdown(extensions=['extra', 'meta', TocExtension(baselevel=2), 'attr_list'])
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
    namespaces = [p.rstrip('-') for p in pad.display_slug.split('::')]

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
                date_parsed = dateutil.parser.parse(date)
                # If there is no timezone we assume it is in Brussels:
                if not date_parsed.tzinfo:
                    date_parsed = pytz.timezone('Europe/Brussels').localize(date_parsed) 
                meta['date_parsed'].append(date_parsed)
                meta['date_iso'].append( date_parsed.isoformat() )

        meta_list = list(meta.items())

        print(meta_list)

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
# def manage(request, page=1):
def manage(request, path=[]):
    if len(path) > 0:
        path = path.split('/')
        pads = Pad.objects.filter(display_slug__startswith='::'.join(path) + '::')
    else:
        pads = Pad.objects.all()
    # paginator = Paginator(pads, PADS_PER_PAGE)

    tree = makeLeaf()

    for pad in pads:
        tree = insertPad(pad, tree)
    
    if len(path) > 0:
        for key in path:
            tree = tree['folders'][key]

        return render(request, "manage-tree.html", {'tree': tree, 'folderPath': path })
    else:
        # return render(request, "manage.html", {'pads': paginator.get_page(page)})
        return render(request, "manage-tree.html", {'tree': tree, 'folderPath': path })

@login_required(login_url='/accounts/login')
def all(request):
    return render(request, "all.html")


def padOrFallbackPath(request, slug, fallbackPath, mimeType):
    try:
        pad = Pad.objects.get(display_slug=slug)
        padID = pad.group.groupID + '$' + urllib.parse.quote(pad.name.replace('::', '_'))
        epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)
        return HttpResponse(epclient.getText(padID)['text'], content_type=mimeType)
    except:
        # If there is no pad called "css", loads a default css file
        f = open(fallbackPath, 'r')
        contents = f.read()
        f.close()
        return HttpResponse(contents, content_type=mimeType)

def css(request):
    return padOrFallbackPath(request, 'screen.css', 'ethertoff/static/css/screen.css', 'text/css')

def cssprint(request):
    return padOrFallbackPath(request, 'laser.css', 'ethertoff/static/css/laser.css', 'text/css')

def offsetprint(request):
    return padOrFallbackPath(request, 'offset.css', 'ethertoff/static/css/offset.css', 'text/css')

def css_slide(request):
    return padOrFallbackPath(request, 'slidy.css', 'ethertoff/static/css/slidy.css', 'text/css')