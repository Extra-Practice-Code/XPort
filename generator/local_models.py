from pydoc import pager
from generator import fields, links
from generator.models import Model, keyFilter
from generator.links import linkMultiReverse, multiLinkMultiReverse, multiLinkReverse
from generator.collection import contentType, InstantiatingCollection
import re
import requests
from django.urls import reverse
from django.core.files.images import ImageFile
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import os.path

from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

VIMEO_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:player\.|www\.)?vimeo\.com\/(?:video\/)?(\d+)', re.I)
YOUTUBE_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:(?:www\.)?youtube\.com\/watch\?v=|youtu\.be\/)([\w\d]+)', re.I)

# FIXME: 

@contentType(InstantiatingCollection)
class Image (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/image.html'
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'image': fields.SingleImageField(),
      'date': fields.Single(fields.DateField()),
      'tags': multiLinkMultiReverse(self, 'tag', 'images'),
      'title': fields.Single(fields.InlineMarkdownField()),
      'author': fields.Single(fields.InlineMarkdownField()),
      'alt': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType(InstantiatingCollection)
class Audio (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/audio.html'

  def _metadataFields (self):
    return {
      'audio': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['audio/mp3'])),
      'date': fields.Single(fields.DateField()),
      'tags': multiLinkMultiReverse(self, 'tag', 'images'),
      'title': fields.Single(fields.InlineMarkdownField()),
      'author': fields.Single(fields.InlineMarkdownField()),
      'alt': fields.Single(fields.InlineMarkdownField()),
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

  """
    If the video is recognized as a youtube video,
    include it using their API.
  """
  @property
  def youtubeId (self):
    # Find more elegant solution?
    video = self.video.value
    if video:
      m = YOUTUBE_VIDEO_URL_PATTERN.match(video)

      if m:
        return m.group(1)
    
    return None

  # @property
  # def thumbnail (self):
  #   if not somehowCached:
  #     if self.vimeoId:
  #       thumbnail = 
      
  #     elif self.youtubeId:
  #       thumbnail = 'http://img.youtube.com/vi/'+self.youtubeId+'/maxresdefault.jpg'

  #     else:
  #       # check cache otherwised generat
  #   else:
  #     image = retreiveFromCache
  #   # Should return an Image()
  
  # @property
  # def thumbnailLink(self):
  #   if self.youtubeId:
  #       return f"http://img.youtube.com/vi/{self.youtubeId}/maxresdefault.jpg"

  #   elif self.vimeoId:
  #       requestLink = f"https://vimeo.com/api/oembed.json?url=http%3A//vimeo.com/{self.vimeoId}"
  #       r = requests.get(requestLink)
  #       return r.json()['thumbnail_url']
  #   else:
  #     return None
  
  # @property
  # def thumb(self):
  #   if self.youtubeId:
  #     file_name = self.youtubeId
  #   elif self.vimeoId:
  #     file_name = self.vimeoId
  #   else:
  #     return None

  #   path = os.path.join(settings.MEDIA_ROOT, "video_thumbnails")

  #   if not os.path.exists(path):
  #     os.makedirs(path)

  #   # if not Path(f"{file_name}.jpg").is_file():
  #   res = requests.get(self.thumbnailLink, stream = True)

  #   if res.status_code == 200:
  #       with open(os.path.join(path, "{}.jpg".format(file_name)),'wb') as f:
  #         file = ImageFile(f)
  #         file.write(res.content)
  #         file.save()
  #       print('Image sucessfully Downloaded: ',file_name)
  #   else:
  #       print('Image Couldn\'t be retrieved')
    
  #   return file

  def _metadataFields (self):
    return {
      'video': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['video/mp4'])),
      'date': fields.Single(fields.DateField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType()
class SharedSpace (Model):
  singlePageTemplate = 'generator/reflection.html'
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'sharedspace': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse(self, 'station', 'sharedspaces'),
      'tags': multiLinkMultiReverse(self, 'tag', 'sharedspaces'),
      'voices': multiLinkMultiReverse(self, 'voice', 'sharedspaces'),
      'summary': fields.Single(fields.SummaryField(model=self))
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
  def padurl (self):
    return reverse('pad', kwargs={'mode': 'w', 'slug': self.source_pad.display_slug})


@contentType(InstantiatingCollection)
class Tag (Model):
  generateListPage = True
  singlePageTemplate = 'generator/tag.html'
  listPageTemplate = 'generator/list--tags.html'
  sortKey = ('first_letter')
  # Use a metaclass to have better default values?

  def _metadataFields (self):
    return {
      'tag': fields.Single(fields.StringField()),
    }

  @property
  def first_letter (self):
    return str(getattr(self, 'tag'))[:1].lower()

@contentType(InstantiatingCollection)
class Voice (Model):
  # Use a metaclass to have better default values?
  generateListPage = True
  singlePageTemplate = 'generator/voice.html'
  listPageTemplate = 'generator/list--voices.html'
  sortKey = ('type', 'sortname')
  groupKey = 'type'

  def _metadataFields (self):
    return {
      'voice': fields.Single(fields.StringField()),
      'sortname': fields.Single(fields.StringField(default=lambda: [self.voice.value], filter=lambda v: v.lower() if v else v)), # bit hacky but self refers to the model. When the field is called it'll lookup the value of voice.
      'status': fields.Single(fields.StringField(default=['draft'])),
      'type': fields.Single(fields.StringField(default=['voice'])),
      'tags': multiLinkMultiReverse(self, 'tag', 'voices'),
      'images': multiLinkMultiReverse(self, 'image', 'voices'),
      'summary': fields.Single(fields.SummaryField(model=self))
    }

@contentType()
class Gallery (Model):
  plural = 'galleries'
  generateListPage = True
  referenceTemplate = 'generator/snippets/references/gallery.html'
  listPageTemplate = 'generator/list--galleries.html'

  sortKey = '-date'
  
  def _metadataFields (self):
    return {
      'gallery': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'images': multiLinkMultiReverse(self, 'image', 'galleries'),
      'videos': multiLinkMultiReverse(self, 'video', 'galleries'),
      'station': linkMultiReverse(self, 'station', 'galleries'),
      'tags': multiLinkMultiReverse(self, 'tag', 'galleries'),
      'voices': multiLinkMultiReverse(self, 'voice', 'galleries')
    }


@contentType()
class Page (Model):
  def _metadataFields (self):
    return {
      'page': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'images': multiLinkMultiReverse(self, 'image', 'pages'),
      'stations': multiLinkMultiReverse(self, 'station', 'pages'),
      'tags': multiLinkMultiReverse(self, 'tag', 'pages'),
      'voices': multiLinkMultiReverse(self, 'voice', 'pages'),
      'contributions': multiLinkMultiReverse(self, 'contribution', 'pages'),
      'reflections': multiLinkMultiReverse(self, 'reflection', 'pages'),
      'previewReviews': multiLinkMultiReverse(self, 'previewReview', 'pages'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'pages'),
      'summary': fields.Single(fields.SummaryField(model=self))
    }


@contentType()
class Station (Model):
  singlePageTemplate = 'generator/station.html'
  sortKey = '-date'
  generateListPage = True
  listPageTemplate = 'generator/list--stations.html'

  def _metadataFields (self):
    return {
      'station': fields.Single(fields.StringField()),
      'shortname': fields.Single(fields.StringField(default=lambda: [self.station.value])),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'summary': fields.Single(fields.SummaryField(model=self)),
      'question': fields.Single(fields.InlineMarkdownField()),
      'date': fields.Single(fields.DateField()),
      'time': fields.TimeField(),
      'location': fields.StringField(),
      'tags': multiLinkMultiReverse(self, 'tag', 'stations'),
      'voices': multiLinkMultiReverse(self, 'voice', 'stations'),
      'images': multiLinkMultiReverse(self, 'image', 'stations'),
      'videos': multiLinkMultiReverse(self, 'video', 'stations'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'stations'),
      'events': multiLinkReverse(self, 'event', 'station')
    }

@contentType(InstantiatingCollection)
class Event (Model):
  sortKey = '-dates'
  # generateSinglePages = False

  def _metadataFields (self):
    return {
      'event': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'dates': fields.DateTimeField(),
      'location': fields.Single(fields.InlineMarkdownField()),
      'summary': fields.Single(fields.SummaryField(model=self)),
      'station': linkMultiReverse(self, 'station', 'events'),
      'voices': multiLinkMultiReverse(self, 'voice', 'events'),
      'images': multiLinkMultiReverse(self, 'image', 'events'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'events')
    }

@contentType()
class Contribution (Model):
  singlePageTemplate = 'generator/reflection.html'
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'contribution': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse(self, 'station', 'contributions'),
      'tags': multiLinkMultiReverse(self, 'tag', 'contributions'),
      'voices': multiLinkMultiReverse(self, 'voice', 'contributions'),
      'summary': fields.Single(fields.SummaryField(model=self)),
      'images': multiLinkMultiReverse(self, 'image', 'contributions'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'contributions')
    }

@contentType()
class Reflection (Model):
  singlePageTemplate = 'generator/reflection.html'
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'reflection': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse(self, 'station', 'reflections'),
      'tags': multiLinkMultiReverse(self, 'tag', 'reflections'),
      'voices': multiLinkMultiReverse(self, 'voice', 'reflections'),
      'summary': fields.Single(fields.SummaryField(model=self)),
      'images': multiLinkMultiReverse(self, 'image', 'reflections'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'reflections')
    }

@contentType()
class PreviewReview (Model):
  singlePageTemplate = 'generator/reflection.html'
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'previewreview': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'status': fields.Single(fields.StringField(default=['draft'])),
      'station': linkMultiReverse(self, 'station', 'previewreviews'),
      'tags': multiLinkMultiReverse(self, 'tag', 'previewreviews'),
      'voices': multiLinkMultiReverse(self, 'voice', 'previewreviews'),
      'summary': fields.Single(fields.SummaryField(model=self)),
      'images': multiLinkMultiReverse(self, 'image', 'previewreviews'),
      'galleries': multiLinkMultiReverse(self, 'gallery', 'previewreviews')
    }
