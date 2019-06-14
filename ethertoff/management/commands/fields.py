FIELD_DATE_FORMAT = '%d-%m-%Y'
FIELD_DATETIME_FORMAT = '%d-%m-%Y %H:%M'
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
    return datetime.datetime.strptime(value, FIELD_DATE_FORMAT).date()

class DateTimeField (Field):
  def parse (self, value):
    return datetime.datetime.strptime(value, FIELD_DATETIME_FORMAT)

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
