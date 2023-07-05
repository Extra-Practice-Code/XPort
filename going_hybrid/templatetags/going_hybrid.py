from django import template
from generator.collection import collectionFor
from generator.settings import SITE_URL

from tags.utils import load_tags

register = template.Library()



@register.inclusion_tag('going-hybrid/snippets/navbar.html')
def going_hybrid_navbar ():
  allowed_tags = load_tags()

  def allowed_tag (tag):
    try:
      if allowed_tags.index(str(tag).lower()) > -1:
        return True
    except ValueError:
      return False

  return {
    'SITE_URL': SITE_URL,
    'tags': [
      tag for tag in filter(allowed_tag, collectionFor('tag'))
    ]
  }
    