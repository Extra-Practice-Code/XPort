from pydoc import pager
from generator import fields, links
from generator.models import Model, keyFilter
from generator.links import linkMultiReverse, multiLinkMultiReverse
from generator.collection import contentType, InstantiatingCollection
import re
from django.urls import reverse

VIMEO_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:player\.|www\.)?vimeo\.com\/(?:video\/)?(\d+)', re.I)

# FIXME: 

@contentType(InstantiatingCollection)
class Image (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/image.html'

  def _metadataFields (self):
    return {
      'image': fields.SingleImageField(),
      'title': fields.Single(fields.InlineMarkdownField()),
      'author': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField()),
    }


@contentType(InstantiatingCollection)
class Audio (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/audio.html'

  def _metadataFields (self):
    return {
      'audio': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['audio/mp3'])),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }

@contentType(InstantiatingCollection)
class Video (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/video.html'

  """
    If the video is recognized as a vimeo video,
    include it using their API.
  """
  @property
  def vimeoId (self):
    # Find more elegant solution?
    video = self.video.value
    if video:
      m = VIMEO_VIDEO_URL_PATTERN.match(video)

      if m:
        return m.group(1)
    
    return None


  def _metadataFields (self):
    return {
      'video': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['video/mp4'])),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType()
class Pad (Model):
  generateSinglePages = False
  
  def _metadataFields (self):
    return {
      'pad': fields.Single(fields.StringField())
    }

  @classmethod
  def extractKey(cls, data):
    if cls.keyField in data:
      return keyFilter(data[cls.keyField])
    elif 'display_slug' in data:
      return keyFilter(data['display_slug'])
    elif 'pk' in data:
      return keyFilter(data['pk'])
    else:
      raise ValueError("Object doesn't have any key")

  def getSortKey(self):
    return self.source_pad.display_slug

  @property
  def url (self):
    return reverse('pad', kwargs={'mode': 'w', 'slug': self.source_pad.display_slug})


@contentType(InstantiatingCollection)
class Tag (Model):
  # Use a metaclass to have better default values?
  singlePageTemplate = 'generator/tag.html'

  def _metadataFields (self):
    return {
      'tag': fields.Single(fields.StringField()),
    }


@contentType(InstantiatingCollection)
class Voice (Model):
  # Use a metaclass to have better default values?

  def _metadataFields (self):
    return {
      'voice': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'tags': multiLinkMultiReverse('tag', 'voices'),
    }



@contentType()
class Gallery (Model):
  def _metadataFields (self):
    return {
      'gallery': fields.Single(fields.StringField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'images': multiLinkMultiReverse('image', 'galleries'),
      'station': linkMultiReverse('station', 'galleries'),
      'tags': multiLinkMultiReverse('tag', 'galleries'),
      'voices': multiLinkMultiReverse('voice', 'galleries')
    }


@contentType()
class Page (Model):
  def _metadataFields (self):
    return {
      'page': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse('station', 'pages'),
      'tags': multiLinkMultiReverse('tag', 'pages'),
      'voices': multiLinkMultiReverse('voice', 'pages')
    }


@contentType()
class Station (Model):
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'station': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'summary': fields.Single(fields.InlineMarkdownField()),
      'date': fields.Single(fields.DateField()),
      'time': fields.TimeField(),
      'location': fields.StringField(),
      'tags': multiLinkMultiReverse('tag', 'stations'),
      'voices': multiLinkMultiReverse('voice', 'stations'),
      'pads': multiLinkMultiReverse('pad', 'stations')
    }

@contentType()
class Contribution (Model):
  def _metadataFields (self):
    return {
      'contribution': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse('station', 'contributions'),
      'tags': multiLinkMultiReverse('tag', 'contributions'),
      'voices': multiLinkMultiReverse('voice', 'contributions')
    }

@contentType()
class Reflection (Model):
  def _metadataFields (self):
    return {
      'reflection': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse('station', 'reflections'),
      'tags': multiLinkMultiReverse('tag', 'reflections'),
      'voices': multiLinkMultiReverse('voice', 'reflections')
    }
