# -*- coding: utf-8 -*-
from .settings import TIME_OUTPUT_FORMAT, FIELD_DATE_FORMATS, FIELD_TIME_FORMAT, DATE_OUTPUT_FORMAT
import datetime
import re
import markdown
from django.utils.safestring import mark_safe

class TimeRange(object):
  def __init__ (self, start, end):
    self.start = start
    self.end = end

  def __str__ (self):
    return '{} - {}'.format(self.start.strftime(TIME_OUTPUT_FORMAT), self.end.strftime(TIME_OUTPUT_FORMAT))


class Time (object):
  def __init__ (self, time):
    self.time = time
  
  def __str__ (self):
    return self.time.strftime(TIME_OUTPUT_FORMAT)


class Date (object):
  def __init__ (self, date):
    self.date = date

  def __str__ (self):
    return '{}'.format(self.date.strftime(DATE_OUTPUT_FORMAT))

class DateRange (object):
  def __init__ (self, start, end):
    self.start = start
    self.end = end
  
  def __str__ (self):
    return '{} - {}'.format(self.start, self.end)

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
    for frm in FIELD_DATE_FORMATS:
      try:
        return datetime.datetime.strptime(value, frm).date()
      except ValueError:
        pass

    return None

class DateTimeField (Field):
  def parse (self, value):
    try:
      return datetime.datetime.strptime(value, '{} {}'.format(FIELD_DATE_FORMAT, FIELD_TIME_FORMAT))
    except ValueError:
      return datetime.datetime.strptime(value, '{} {}'.format(FIELD_DATE_FORMAT_ALT, FIELD_TIME_FORMAT))

class TimeField (Field):
  def parse (self, value):
    m = re.match(r'(\d{1,2}\:\d{1,2})\s*[-|―|─]\s*(\d{1,2}\:\d{1,2})', value)
    if m:
      start = datetime.datetime.strptime(m.group(1), FIELD_TIME_FORMAT).time()
      end = datetime.datetime.strptime(m.group(2), FIELD_TIME_FORMAT).time()
      return TimeRange(start, end)
    else:
      return Time(datetime.datetime.strptime(value, FIELD_TIME_FORMAT).time())

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