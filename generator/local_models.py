from generator.utils import debug
from generator import fields
from generator.models import Model, keyFilter
from generator.links import linkMultiReverse, multiLinkMultiReverse, multiLinkReverse
from generator.collection import contentType, InstantiatingCollection
import re
import requests
from django.urls import reverse
from django.core.files.images import ImageFile
from django.conf import settings
import os
import os.path
from time import sleep

VIMEO_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:player\.|www\.)?vimeo\.com\/(?:video\/)?(\d+)', re.I)
YOUTUBE_VIDEO_URL_PATTERN = re.compile('(?:https?:\/\/)?(?:(?:www\.)?youtube\.com\/watch\?v=|youtu\.be\/)([\w\d]+)', re.I)

# FIXME: 

@contentType(InstantiatingCollection)
class Image (Model):
  generateSinglePages = False
  sortKey = '-date'

  def _metadataFields (self):
    return {
      'image': fields.SingleImageField(),
      'date': fields.Single(fields.DateField()),
      'labels': multiLinkMultiReverse(self, 'label', 'images'),
      'title': fields.Single(fields.InlineMarkdownField()),
      'author': fields.Single(fields.InlineMarkdownField()),
      'alt': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType(InstantiatingCollection)
class Audio (Model):
  generateSinglePages = False

  def _metadataFields (self):
    return {
      'audio': fields.SingleFileField(),
      'type': fields.Single(fields.StringField(['audio/mp3'])),
      'date': fields.Single(fields.DateField()),
      'labels': multiLinkMultiReverse(self, 'label', 'images'),
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

  @property
  def _thumbnailRemoteURL(self):
    if self.youtubeId:
      return "http://img.youtube.com/vi/{}/maxresdefault.jpg".format(self.youtubeId)

    elif self.vimeoId:
      requestURL = "https://vimeo.com/api/oembed.json?url=http%3A//vimeo.com/{}".format(self.vimeoId)

      for _ in range(5):
        try:
          r = requests.get(requestURL)
          return r.json()['thumbnail_url']
        finally:
          debug("Could not retreive Vimeo thumbnail with {}".format(requestURL))
          sleep(.25)
          pass
    else:
      return None
  
  @property
  def thumbnailPath (self):
    if self.youtubeId:
      filename = '{}.jpg'.format(self.youtubeId)
    elif self.vimeoId:
      filename = '{}.jpg'.format(self.vimeoId)
    else:
      return None


    thumbnail_dir = "video_thumbnails"
    thumbnail_path = os.path.join(thumbnail_dir, filename)

    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, thumbnail_dir)):
      os.makedirs(os.path.join(settings.MEDIA_ROOT, thumbnail_dir))

    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, thumbnail_path)):
      url = self._thumbnailRemoteURL
      res = requests.get(url, stream = True)
      if res.status_code == 200:
        with open(os.path.join(settings.MEDIA_ROOT, thumbnail_path),'wb') as f:
          f.write(res.content)
          f.close()
          
      else:
          print('Image Couldn\'t be retrieved')
    
    # with open(os.path.join(thumbnail_path, 'rb')) as f:
    # file = ImageFile(f)

    return thumbnail_path

  @property
  def thumbnailURL (self):
    return settings.MEDIA_URL + self.thumbnailPath()

  def _metadataFields (self):
    return {
      'video': fields.Single(fields.StringField()),
      'type': fields.Single(fields.StringField(['video/mp4'])),
      'date': fields.Single(fields.DateField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType(InstantiatingCollection)
class Youtube (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/video--youtube.html'

  def _metadataFields (self):
    return {
      'youtube': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType(InstantiatingCollection)
class Vimeo (Model):
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/video--vimeo.html'

  def _metadataFields (self):
    return {
      'vimeo': fields.Single(fields.StringField()),
      'date': fields.Single(fields.DateField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField())
    }


@contentType(InstantiatingCollection)
class Label (Model):
  generateListPage = True
  generateSinglePages = True
  singlePageTemplate = 'generator/label.html'
  referenceTemplate = 'generator/snippets/references/label.html'
  sortKey = ('first_letter')
  # Use a metaclass to have better default values?

  def _metadataFields (self):
    return {
      'label': fields.Single(fields.StringField()),
    }

  @property
  def first_letter (self):
    return str(getattr(self, 'label'))[:1].lower()

@contentType(InstantiatingCollection)
class Annotation (Model):
  generateListPage = False
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/annotation.html'
  sortKey = ('first_letter')
  # Use a metaclass to have better default values?

  def _metadataFields (self):
    return {
      'annotation': fields.Single(fields.InlineMarkdownField()),
      'author': fields.Single(fields.InlineMarkdownField(default=[None]))
    }
  
  @property
  def annotation_type (self):
    if getattr(self, 'author').value is not None:
      return 'annotation'
    else:
      return 'reference'

  @property
  def first_letter (self):
    return str(getattr(self, 'annotation'))[:1].lower()


@contentType(InstantiatingCollection)
class Author (Model):
  generateListPage = False
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/author.html'
  sortKey = ('first_letter')
  # Use a metaclass to have better default values?

  def _metadataFields (self):
    return {
      'author': fields.Single(fields.InlineMarkdownField()),
    }

  @property
  def first_letter (self):
    return str(getattr(self, 'author'))[:1].lower()


@contentType()
class Report (Model):
  generateListPage = True
  generateSinglePages = True
  
  sortKey = 'order'

  def _metadataFields (self):
    return {
      'report': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['published'])),
      'order': fields.Single(fields.IntField(default=[99999])), 
      'labels': multiLinkMultiReverse(self, 'label', 'reports', unique=False)
    }



@contentType()
class Pad (Model):
  generateListPage = True
  generateSinglePages = True

  def _metadataFields (self):
    return {
      'pad': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['published'])),
      'labels': multiLinkMultiReverse(self, 'label', 'reports', unique=False),
      'title': fields.Single(fields.InlineMarkdownField()),
      'index': fields.Single(fields.StringField(default=['false']))
    }
  

# @FIXME chapter | page | section | part
@contentType()
class Chapter (Model):
  generateSinglePages = True
  
  sortKey = 'order'

  def _metadataFields(self):
    return {
      'chapter': fields.Single(fields.StringField()),
      'status': fields.Single(fields.StringField(default=['published'])),
      'order': fields.Single(fields.IntField()),
      'position': fields.Single(fields.StringField(default=['before_content'])),
      'on_print': fields.Single(fields.StringField(default=['true'])),
      'on_web': fields.Single(fields.StringField(default=['true'])),
      'labels': multiLinkMultiReverse(self, 'label', 'chapters', unique=False)
    }
  