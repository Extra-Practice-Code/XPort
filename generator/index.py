from generator.collection import collectionFor, contentType, knownContentTypes
from generator.links import is_link, is_multi_link, is_reverse_link, is_reverse_multi_link
from generator.settings import PAD_BASE_URL
import os.path

LINK_DIRECTION_OUT = 'out'
LINK_DIRECTION_IN = 'in'

def display_field (field):
  return '<dd class="attribute">{label}</dd>'.format(label=str(field))

def display_url (field):
  return '<dd class="attribute"><a href="{label}">{label}</a></dd>'.format(label=str(field))

def display_empty ():
  return '<dd class="attribute empty-attribute">not set</dd>'.format()

# def display_link (direction = LINK_DIRECTION_OUT, label, url=None):
# The source is already listed, so we care about the target
def display_link (link):
  if not link:
    return display_empty()

  if link.reverse:
    direction = LINK_DIRECTION_IN
  else:
    direction = LINK_DIRECTION_OUT

  arrow = '→' if direction == LINK_DIRECTION_OUT else '←'
  
  # Label of target?
  # If there is a sourcepath include it as well
  # Mark whether it is an inline link

  if link.broken:
    return '<dd class="link link-broken">{direction} {arrow} {label} ({contentType}) [broken, unable to resolve]</dd>'.format(
      direction=direction,
      arrow=arrow,
      label=link.target,
      contentType=link.contentType
    )
  elif not link.resolved:
    return '<dd class="link link-unresolved">{direction} {arrow} {label} ({contentType}) [unresolved]</dd>'.format(
      direction=direction,
      arrow=arrow,
      label=link.target,
      contentType=link.contentType
    )
  else:
    return '<dd>{direction} {arrow} <a href="#{id}">{label}</a> ({contentType})</dd>'.format(
        direction=direction,
        arrow=arrow,
        label=str(link.target),
        id=link.target._id,
        contentType=link.contentType
      )

def make_index (models):
  buff = '<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head><body>'
  buff += '<h1>Debug / data overview</h1>'
  for contentType in knownContentTypes():
    buff += '<details open><summary><strong>{}</strong></summary>'.format(contentType)
    collection = collectionFor(contentType)
    for obj in collection.models:
      buff += '<details id="{}">'.format(obj._id)
      # Object has a real pad attached
      if obj.source_path:
        buff += '<summary><strong>{label}</strong> <a href="{link}">(pad)</a></summary>'.format(
          label=str(obj),
          type=obj.contentType,
          link=os.path.join(PAD_BASE_URL, obj.source_path.replace('#', '%23'))
        )
      else:
        buff += '<summary><strong>{label}</strong></summary>'.format(
          label=str(obj),
          type=obj.contentType
        )

      buff += '<dl>'
      for attr in dir(obj):
        if attr != 'content':
          # Attributes noted in the metafields list, plus content,
          # the link property and the sourcepath
          buff += '<dt>{attr}</dt>'.format(attr=attr)
          if attr == 'links':
            for link in getattr(obj, attr):
              buff += display_link(link)
          elif hasattr(obj, attr):
            field = getattr(obj, attr)
            if is_multi_link(field) or is_reverse_multi_link(field):
              for link in field.value:
                buff += display_link(link)
            elif is_link(field) or is_reverse_link(field):
              buff += display_link(field.value)
            elif attr  == 'url':
              buff += display_url(field)
            else:
              buff += display_field(field)
          else:
            buff += display_empty()

        # if attr in obj.metadata \
        #   and is_link(obj.metadata[attr]):
        #   val = getattr(obj, attr)
        #   buff += '<dt>{}</dt>'.format(attr)

        #   # print('Outgoing link(s)', attr)
        #   if type(val) is list:
        #     for entry in val:
        #       if isinstance(entry, Model):
        #         buff += display_link('out', try_attributes(entry, [entry.labelField, 'pk']), entry.source_path)
        #   elif isinstance(val, Model):
        #     buff += display_link('out', try_attributes(val, [val.labelField, 'pk']), val.source_path)


        # # As the attribute is not in the metadataFields
        # # it almost certainly is an incoming link 
        # elif not attr in obj.metadata and attr not in ['pk', 'content', 'source_path']:
        #   val = getattr(obj, attr)
        #   buff += '<dt>{}</dt>'.format(attr)
        #   if type(val) is list:
        #     for entry in val:
        #       if isinstance(entry, Model):
        #         buff += display_link('in', try_attributes(entry, [entry.labelField, 'pk']), entry.source_path)
        #   elif isinstance(val, Model):
        #     buff += display_link('in', try_attributes(val, [val.labelField, 'pk']), val.source_path)

      buff += '</dl>'
      buff += '</details>'
    buff += '</details>'
  buff += """<style>
details {
	padding-left: 2em;
	padding-bottom: 2em;
}
summary {
	margin-left: -2em;
	margin-bottom: 1em;
}
body {
	margin: 2em 3em;
}
</style></body></html>"""

  return buff
