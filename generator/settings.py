from ethertoff.settings import DEBUG

MENU_ITEMS = [
  ('About', 'pages/about.html'),
  ('Activities', 'activities.html'),
  ('Artist trajectories', 'trajectories.html'),
  ('Produsers', 'produsers.html' ),
  ('Bibliography', 'bibliography.html' ),
  ('Projects & Initiatives', 'external-projects.html'),
  ('Tags', 'tags.html' ),
  ('Contact', 'pages/contact.html')
]

SITE_URL = ''
DEFAULT_CONTENT_TYPE = 'pad'
SHOW_LOG_MESSAGES = True
SHOW_DEBUG_MESSAGES = True

FIELD_DATE_FORMATS = ['%d-%m-%Y', '%d %b %Y']
FIELD_TIME_FORMAT = '%H:%M'

TIME_OUTPUT_FORMAT = '%H:%M'

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass