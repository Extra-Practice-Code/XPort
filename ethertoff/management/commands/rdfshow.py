from django.core.management.base import BaseCommand
from etherpadlite.models import Pad
from django.contrib.sites.models import Site
from django.urls import reverse
from aasniff import AAApp
import rdflib


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
        app = AAApp(conf=Conf)
        # print(rt)

        # for quad in graph.quads():
        #     print(quad)

        node = rdflib.URIRef("http://purl.org/dc/terms/title")
        NS = {
            'bibo': rdflib.Namespace("http://purl.org/ontology/bibo/"),
            'bib': rdflib.Namespace("http://purl.org/net/biblio#"),
            'dc': rdflib.namespace.DC,
            'dcterms': rdflib.namespace.DCTERMS,
            'egr2': rdflib.Namespace("http://rdvocab.info/ElementsGr2/"),
            'foaf': rdflib.namespace.FOAF,
            'frbr': rdflib.Namespace("http://purl.org/vocab/frbr/core#"),
            'purl': rdflib.Namespace("http://purl.org/dc/terms/"),
            'rdf': rdflib.RDF,
            'rdvocab': rdflib.Namespace("http://RDVocab.info/elements/"),
            'stats': rdflib.Namespace("http://kavan.land/vocab/stats#"),
            'vocab': rdflib.Namespace("http://purl.org/vocab/frbr/core#"),
            'wemi': rdflib.Namespace("http://RDVocab.info/RDARelationshipsWEMI/"),
            'z': rdflib.Namespace("http://www.zotero.org/namespaces/export#"),
        }

        as_predicate = app.graph.query("""
            SELECT DISTINCT ?subject ?title
            WHERE {
                ?subject dcterms:title ?title.
            }
        """, initBindings={'predicate': node}, initNs=NS)

        print(as_predicate)
        for i in as_predicate:
            print(i[1])


