FIELD_DATE_FORMAT = '%d-%m-%Y'
FIELD_DATE_FORMAT_ALT = '%d %b %Y'
FIELD_TIME_FORMAT = '%H:%M'

import datetime

import markdown
from django.utils.safestring import mark_safe

class Field (object):
  def __init__ (self, default = []):
    self.default = default

  # no-op
  def parse (self, value):
    return value

  def __call__ (self, value):
    if value:
      return [self.parse(v) for v in value]
    else:
      return self.default

"""
  Wrapper for a field object to turn it into a single field
"""
class Single(object):
  def __init__ (self, field):
    self.field = field
  
  def __call__ (self, value):
    result = self.field(value)

    if len(result) > 0:
      return result[0]
    else:
      return None


class DateField (Field):
  def parse (self, value):
    try:
      return datetime.datetime.strptime(value, FIELD_DATE_FORMAT).date()
    except ValueError:
      return datetime.datetime.strptime(value, FIELD_DATE_FORMAT_ALT).date()

class DateTimeField (Field):
  def parse (self, value):
    try:
      return datetime.datetime.strptime(value, '{} {}'.format(FIELD_DATE_FORMAT, FIELD_TIME_FORMAT))
    except ValueError:
      return datetime.datetime.strptime(value, '{} {}'.format(FIELD_DATE_FORMAT_ALT, FIELD_TIME_FORMAT))

class TimeField (Field):
  def parse (self, value):
    return datetime.datetime.strptime(value, FIELD_TIME_FORMAT).time()

class IntField (Field):
  def parse (self, value):
    return int(value)

class FloatField(Field):
  def parse (self, value):
    return float(value)

class StringField(Field):
  def parse (self, value):
    return str(value)

class MarkdownField(Field):
  def parse (self, value):
    md = markdown.Markdown(extensions=['extra', 'attr_list'])
    return mark_safe(md.convert(value))

# # Maybe simplify to a function
# class InlineLink(Field):
#   def __init__ (self, target, label):
#     self.target = target
#     self.label = label

#   def __str__  (self):
#     # return '[{}]({}){{: .{}}}'.format(self.label, self.target.link, self.target.contentType)
#     return '<a href="{target}" class="{className}">{label}</a>'.format(label=self.label, target=self.target.link, className=self.target.contentType)