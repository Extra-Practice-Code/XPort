from django.core.management.base import BaseCommand
from etherpadlite.models import Pad
from django.contrib.sites.models import Site
from django.urls import reverse
from aasniff import AAApp
import markdown
from markdown.extensions.toc import TocExtension


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

        for pad in Pad.objects.filter():
            # TODO: make a Pad method for that 
            client = pad.epclient
            pad_id = pad.padid
            text = client.getText(pad_id)['text']

            path = reverse('pad-read', kwargs={'mode': 'r', 'slug': pad.display_slug})

            # FIXME: handle https as well
            url = f"http://{domain}{path}"
            md = markdown.Markdown(extensions=['extra', 'meta', TocExtension(baselevel=2), 'attr_list'])
            text = md.convert(text)

            html = f"""<!DOCTYPE html>
            <html lang="en">
              <head>
                <title>Example Document</title>
              </head>
              <body>
              {text}
              </body>
            </html>"""

            print(html)

            # print(f"parsing {url}")
            # app.graph.parse(data=html, format="rdfa", publicID=url)
