from generator.models import collectionFor, knownContentTypes, is_link, Model
from generator.utils import try_attributes

def display_link (direction, label, link=None):
  arrow = '→' if direction == 'out' else '←'
  if link:
    return '<dd>{direction} {arrow} <a href="https://ethertoff.caveat.be/w/{link}">{label}</a></dd>'.format(
        direction=direction,
        arrow=arrow,
        label=label,
        link=link.replace('#', '%23')
      )
  else:
    return '<dd>{direction} {arrow} {label}</dd>'.format(
        direction=direction,
        arrow=arrow,
        label=label,
      )

def make_index (models):
  buff = '<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head><body><ul>'
  for contentType in knownContentTypes:
    collection = collectionFor(contentType)
    for obj in collection.models:
      if obj.source_path:
        buff += '<li><a href="https://ethertoff.caveat.be/w/{link}">{label}</a> ({type})'.format(
          label=str(obj),
          type=obj.contentType,
          link=obj.source_path.replace('#', '%23')
        )
      else:
        buff += '<li>{label} ({type})'.format(
          label=str(obj),
          type=obj.contentType
        )
      for attr in dir(obj):
        # Attributes noted in the metafields list
        # can be an outgoing links
        if attr in obj.metadataFields \
          and is_link(obj.metadataFields[attr]):
          val = getattr(obj, attr)
          buff += '<dt>{}</dt>'.format(attr)

          # print('Outgoing link(s)', attr)
          if type(val) is list:
            for entry in val:
              if isinstance(entry, Model):
                buff += display_link('out', try_attributes(entry, [entry.labelField, 'pk']), entry.source_path)
          elif isinstance(val, Model):
            buff += display_link('out', try_attributes(val, [val.labelField, 'pk']), val.source_path)


        # As the attribute is not in the metadataFields
        # it almost certainly is an incoming link 
        elif not attr in obj.metadataFields and attr not in ['pk', 'content', 'source_path']:
          val = getattr(obj, attr)
          buff += '<dt>{}</dt>'.format(attr)
          if type(val) is list:
            for entry in val:
              if isinstance(entry, Model):
                buff += display_link('in', try_attributes(entry, [entry.labelField, 'pk']), entry.source_path)
          elif isinstance(val, Model):
            buff += display_link('in', try_attributes(val, [val.labelField, 'pk']), val.source_path)
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