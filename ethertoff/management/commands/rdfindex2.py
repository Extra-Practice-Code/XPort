from django.core.management.base import BaseCommand
from etherpadlite.models import Pad
from django.contrib.sites.models import Site
from django.urls import reverse
from aasniff import AAApp
import markdown
from markdown.extensions.toc import TocExtension
from django.test import Client
import html5lib
from rdflib.plugins.memory import IOMemory
import rdflib


def tidy(string):
    parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
    dom = parser.parse(string)

    # FIXME: remove this? we moved to rdflib
    # Redland crashes if no xmlns attribute is declared.
    # see: http://bugs.librdf.org/mantis/view.php?id=521
    # Lets fix it in the meanwhile...
    elt = dom.getElementsByTagName("html")[0]
    if not elt.hasAttribute("xmlns"):
        elt.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")

    return dom.toxml()


class Conf(object):
    SNIFFERS = [
        'HttpSniffer',
        'HtmlSniffer',
    ]

    STORE = {
        'ENGINE': 'sqlite',
        'NAME': 'aasniff.sqlite',
    }


class Command(BaseCommand):
    args = ''
    help = 'Indexes pages'

    def handle(self, *args, **options):
        from django.contrib.sites.models import Site
        domain = Site.objects.get_current().domain

        app = AAApp(conf=Conf)

        # store = IOMemory()
        # graph = rdflib.graph.ConjunctiveGraph(store=store)

        for pad in Pad.objects.filter():
            c = Client()
            path = reverse('pad-read', kwargs={'mode': 'r', 'slug': pad.display_slug})
            response = c.get(path)
            url = f"http://{domain}{path}"
            
            print(f"parsing {url}")
            if response.status_code == 200:
                try:
                    app.graph.parse(data=tidy(response.content), format="rdfa", publicID=url)
                except:
                    print(f"couldn't parse {url}")
            else:
                print(f"failed to parse {url}")


        # for quad in graph.quads():
        #     # avoids duplicates statements
        #     app.graph.remove(quad)
        #     # adds the new statements
        #     app.graph.add(quad)
