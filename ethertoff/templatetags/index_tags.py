from django import template
from aasniff import AAApp

register = template.Library()


class Conf(object):
    SNIFFERS = [
        'HttpSniffer',
        'HtmlSniffer',
    ]

    STORE = {
        'ENGINE': 'sqlite',
        'NAME': 'aasniff.sqlite',
    }


@register.inclusion_tag('partials/all_authors.html')
def all_authors():
    app = AAApp(conf=Conf)
    query = app.graph.query("""
        SELECT DISTINCT ?object
        WHERE {
            ?subject <http://purl.org/dc/terms/contributor> ?object.
        }
    """)
    return { "authors": query }
