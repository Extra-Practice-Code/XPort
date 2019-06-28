from ethertoff.settings import DEBUG

MENU_ITEMS = [
  ('About', 'pages/about.html'),
  ('Produsers', 'produsers.html' ),
  ('Bibliography', 'bibliography.html' ),
  ('Tags', 'tags.html' ),
  ('Contact', 'pages/contact.html')
]

SITE_URL = ''
DEFAULT_CONTENT_TYPE = 'pad'
SHOW_LOG_MESSAGES = True
SHOW_DEBUG_MESSAGES = True

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass