from ethertoff.settings import DEBUG

MENU_ITEMS = [
  ('About', 'pages/about.html'),
  ('Produsers', 'produsers.html' ),
  ('Bibliography', 'bibliography.html' ),
  ('Tags', 'tags.html' ),
  ('Contact', 'pages/contact.html')
]

SITE_URL = ''

SHOW_LOG_MESSAGES = DEBUG
SHOW_DEBUG_MESSAGES = DEBUG

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass