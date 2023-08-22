from django import template
from generator.collection import collectionFor

from labels.utils import load_labels

register = template.Library()



@register.inclusion_tag('going-hybrid/snippets/navbar.html', takes_context=True)
def going_hybrid_navbar (context):
  return {
    'SITE_URL': context['SITE_URL'],
    'labels': [
      label for label in filter(lambda label: label in context['LABELS'], collectionFor('label'))
    ]
  }