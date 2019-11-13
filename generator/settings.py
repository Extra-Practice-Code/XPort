MENU_ITEMS = [
  ('About & Contact', 'pages/about.html'),
  ('Timeline', 'index.html'),
  ('Research trajectories', 'trajectories.html'),
  ('Produsers', 'produsers.html' ),
#   ('Bibliography', 'bibliography.html' ),
#   ('Related Projects', 'external-projects.html'),
  ('Tags', 'tags.html' ),
#   ('Contact', 'pages/contact.html')
]

SITE_URL = ''
DEFAULT_CONTENT_TYPE = 'pad'
SHOW_LOG_MESSAGES = True
SHOW_DEBUG_MESSAGES = True

FIELD_DATE_FORMATS = ['%d-%m-%Y', '%d %m %Y', '%d/%m/%Y', '%d %b %Y', '%d %B %Y']
FIELD_TIME_FORMAT = '%H:%M'

TIME_OUTPUT_FORMAT = '%H:%M'
DATE_OUTPUT_FORMAT = '%-d %b %Y'

DATE_OUTPUT_FORMAT_DATE = '%-d'
DATE_OUTPUT_FORMAT_MONTH = '%b'
DATE_OUTPUT_FORMAT_YEAR = '%Y'

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass
