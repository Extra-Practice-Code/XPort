from generator.models import collectionFor, knownContentTypes, \
  is_link, is_multi_link, is_reverse_link, is_reverse_multi_link, \
  Model
from generator.utils import try_attributes

LINK_DIRECTION_OUT = 'out'
LINK_DIRECTION_IN = 'in'

def display_field (field):
  return '<dd class="attribute">{label}</dd>'.format(label=str(field))

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
    return '<dd class="link link-broken">{direction} {arrow} {label} [broken, unable to resolve]</dd>'.format(
      direction=direction,
      arrow=arrow,
      label=link.target
    )
  elif not link.resolved:
    return '<dd class="link link-unresolved">{direction} {arrow} {label} [unresolved]</dd>'.format(
      direction=direction,
      arrow=arrow,
      label=link.target
    )
  else:
    padname = link.target.source_path

    if padname:
      return '<dd>{direction} {arrow} <a href="https://ethertoff.caveat.be/w/{padname}">{label}</a></dd>'.format(
          direction=direction,
          arrow=arrow,
          label=str(link.target),
          padname=padname.replace('#', '%23')
        )
    else:
      return '<dd>{direction} {arrow} {label}</dd>'.format(
          direction=direction,
          arrow=arrow,
          label=str(link.target),
        )

def make_index (models):
  buff = '<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head><body><ul>'
  for contentType in knownContentTypes():
    collection = collectionFor(contentType)
    for obj in collection.models:
      if obj.source_path:
        buff += '<li><strong><a href="https://ethertoff.caveat.be/w/{link}">{label}</a></strong> ({type})'.format(
          label=str(obj),
          type=obj.contentType,
          link=obj.source_path.replace('#', '%23')
        )
      else:
        buff += '<li><strong>{label}</strong>({type})'.format(
          label=str(obj),
          type=obj.contentType
        )
      for attr in dir(obj):
        if attr != 'content':
          # Attributes noted in the metafields list, plus content,
          # the link property and the sourcepath
          buff += '<dt>{attr}</dt>'.format(attr=attr)
          if hasattr(obj, attr):
            field = getattr(obj, attr)
            if is_multi_link(field) or is_reverse_multi_link(field):
              for link in field.value:
                buff += display_link(link)
            elif is_link(field) or is_reverse_link(field):
              buff += display_link(field.value)
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
      buff += '</li>'
  buff += '</ul><style>li { margin-top: 1em; }</style></body></html>'
  return buff
# for obj in models:
#   '{type}: {label} -- {padurl}'.format({ 'type': obj.type, 'label': getattr(obj, obj.labelField), 'padurl': padurl })
#   for (prop, val) in dir(obj):
#     if is_link(val):
#       print('{targetname}: {targetcontenttype} {targetgcontentpadurl}').format({
#         'targetname': '',
#         'targetcontenttype': '',
#         'targetgcontentpadurl': ''
#       })\\\