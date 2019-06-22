MENU_ITEMS = [
  ('About', 'pages/about.html'),
  ('Produsers', 'produsers.html' ),
  ('Contact', 'contact.html')
]

SITE_URL = ''

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass