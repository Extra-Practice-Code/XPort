from django import template
from generator.collection import collectionFor

from labels.utils import load_labels

register = template.Library()



@register.inclusion_tag('going-hybrid/snippets/navbar.html', takes_context=True)
def going_hybrid_navbar (context):
  allowed_labels = load_labels()

  def allowed_label (label):
    try:
      if allowed_labels.index(str(label).lower()) > -1:
        return True
    except ValueError:
      return False

  return {
    'SITE_URL': context['SITE_URL'],
    'labels': [
      label for label in filter(allowed_label, collectionFor('label'))
    ]
  }