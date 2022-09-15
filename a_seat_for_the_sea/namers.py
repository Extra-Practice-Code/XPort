from easy_thumbnails.namers import hashed

def hashed_force_gif_on_dither (source_filename, prepared_options, thumbnail_extension, **kwargs):
  """
  Generate a short hashed thumbnail filename.
  
  Creates a 12 character url-safe base64 sha1 filename (plus the extension),
  for example: ``6qW1buHgLaZ9.jpg``.
  """
  
  for option in prepared_options:
    if option.startswith('dither'):
      thumbnail_extension = 'gif'
  
  return hashed(source_filename, prepared_options, thumbnail_extension, **kwargs)
