from django.core.management.base import BaseCommand
from etherpadlite.models import Pad
from django.contrib.sites.models import Site
from django.urls import reverse
from aasniff import AAApp


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
        HOST = None

        if Site.objects.count() > 0:
            site = Site.objects.all()[0]
            HOST = site.domain

        if not HOST:
            return "No site domain settings found"

        host = u"http://%s" % HOST

        app = AAApp(conf=Conf)

        for pad in Pad.objects.filter():
            url = "{}{}".format(host, reverse('pad-read', kwargs={'mode': 'r', 'slug': pad.display_slug}))
            try:
                app.index(url)
                print(f"indexed {url}")
            except:
                print(f"fail at indexing {url}")



