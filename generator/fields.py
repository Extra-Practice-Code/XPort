# -*- coding: utf-8 -*-
from generator.settings import TIME_OUTPUT_FORMAT, FIELD_DATE_FORMATS, FIELD_TIME_FORMAT, DATE_OUTPUT_FORMAT, DATE_OUTPUT_FORMAT_DATE, DATE_OUTPUT_FORMAT_MONTH, DATE_OUTPUT_FORMAT_YEAR
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
    # return '{} - {}'.format(self.start, self.end)

    delta = (self.end.date - self.start.date).days + 1
    
    if delta > 3:
      return ' ― '.join(self.makeFormattingChunks([self.start.date, self.end.date]))
    else:
      chunks = self.makeFormattingChunks([self.start.date + datetime.timedelta(days=k) for k in range(delta)])
      if delta > 2:
        return ', '.join(chunks[:-1]) + ' & ' + chunks[-1]
      else:
        return ' & '.join(chunks)


  def makeFormattingChunks(self, dates):
    chunks = []
    last = None

    # Loop through a reversed list of dates
    # if the month or year changes, add it
    # to the text chunk
    for date in reversed(dates):
      chunk = date.strftime(DATE_OUTPUT_FORMAT_DATE)

      if not last or last.month != date.month:
        chunk += ' ' + date.strftime(DATE_OUTPUT_FORMAT_MONTH)

        if not last or last.year != date.year:
          chunk += ' ' + date.strftime(DATE_OUTPUT_FORMAT_YEAR)

      chunks.append(chunk)

      last = date

    return list(reversed(chunks))

class Field (object):
  def __init__ (self, default = [], filter = None):
    self.default = default
    self._value = None
    self.filter = filter

  # no-op
  def parse (self, value):
    return value

  def set (self, value):
    self._value = [self.parse(v) for v in value]

  def __repr__ (self):
    return repr(self.value)

  def __str__ (self):
    if self.value:
      return str(self.value)
    else:
      return ''

  def __iter__ (self):
    return iter(self.value)
  
  @property
  def value (self):
    if self._value:
      if self.filter and callable(self.filter):
        return list(map(self.filter, self._value))
      
      return self._value
    else:
      return self.default

  # def __call__ (self, value):
  #   if value:
  #     return [self.parse(v) for v in value]
  #   else:
  #     return self.default

"""
  Wrapper for a field object to turn it into a single field
"""
class Single(object):
  def __init__ (self, field):
    self.field = field
  
  def set (self, value):
    self.field.set(value)

  @property
  def value (self):
    if self.field.value:
      return self.field.value[0]
    else:
      return None

  def __repr__ (self):
    return repr(self.value)

  def __str__ (self):
    return str(self.value)


class DateField (Field):
  def isRange (self, value):
    """
      
      A date is:
      - one or two numbers, day
      - followed by numbers or a word, month
      - followed by two or four numbers, year

      In between the parts a space, hyphen or slash,
      a backreference \2 is used through the regex
      to make sure this seperator is uniform.

      In between the two dates there is a seperator as well,
        group 1 → first date
        group 2 → seperator within the date part
        group 3 → second date part
        
    """
    rangeRegex = r'((?:\d{1,2})(\s|-|─|/)(?:\d{1,2}|\w+)\2(?:\d{2,4}))\s*(?:(?:-|─*)\s*)?((?:\d{1,2})\2(?:\d{1,2}|\w+)\2(?:\d{2,4}))'

    m = re.match(rangeRegex, value)

    if m:
      return (m.group(1), m.group(3))
    else:
      return None

  def parse (self, value):
    dateRange = self.isRange(value)

    if dateRange:
      start, end = dateRange
      return DateRange(self.parse(start), self.parse(end))
    else:
      for date_format in FIELD_DATE_FORMATS:
        try:
          date = datetime.datetime.strptime(value, date_format).date()
          return Date(date)
        except ValueError:
          pass

      return None


class DateTimeField (Field):
  def parse (self, value):
    for date_format in FIELD_DATE_FORMATS:
      try:
        return datetime.datetime.strptime(value, '{} {}'.format(date_format, FIELD_TIME_FORMAT))
      except ValueError:
        pass

    return None

class TimeField (Field):
  def parse (self, value):
    m = re.match(r'(\d{1,2}\:\d{1,2})\s*[-|―|─|→]\s*(\d{1,2}\:\d{1,2})', value)
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
    if value:
      return str(value)
    else:
      return None

class MarkdownField(Field):
  def parse (self, value):
    md = markdown.Markdown(extensions=['extra', 'attr_list'])
    return mark_safe(md.convert(value))

class InlineMarkdownField(Field):
  def parse (self, value):
    md = markdown.Markdown(extensions=['extra', 'attr_list'])
    return mark_safe(re.sub(r'<p>(.+)</p>', '\\1', md.convert(value)))

# # Maybe simplify to a function
# class InlineLink(Field):
#   def __init__ (self, target, label):
#     self.target = target
#     self.label = label

#   def __str__  (self):
#     # return '[{}]({}){{: .{}}}'.format(self.label, self.target.link, self.target.contentType)
#     return '<a href="{target}" class="{className}">{label}</a>'.format(label=self.label, target=self.target.link, className=self.target.contentType)