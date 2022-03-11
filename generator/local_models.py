from generator import fields, links
from generator.models import Model
from generator.collection import contentType, InstantiatingCollection
import re

VIMEO_VIDEO_URL_PATTERN = re.compile('https:\/\/(?:player\.|www\.)?vimeo\.com\/(?:video\/)?(\d+)', re.I)

@contentType(InstantiatingCollection)
class Image (Model):
  contentType = 'image'
  keyField = 'image'
  labelField = 'image'
  generateSinglePages = False
  referenceTemplate = 'generator/snippets/references/image.html'

  def _metadataFields (self):
    return {
      'image': fields.Single(fields.StringField()),
      'title': fields.Single(fields.InlineMarkdownField()),
      'caption': fields.Single(fields.InlineMarkdownField()),
    }


@contentType(InstantiatingCollection)
class Audio (Model):
  contentType = 'audio'
  keyField = 'audio'
  labelField = 'audio'
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
  contentType = 'video'
  keyField = 'video'
  labelField = 'video'
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
class Voice (Model):
  contentType = 'voice'
  keyField = 'voice'
  labelField = 'voice'

  def _metadataFields (self):
    return {
      'voice': fields.Single(fields.StringField()),
    }

