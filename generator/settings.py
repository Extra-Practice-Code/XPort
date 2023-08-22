MENU_ITEMS = [
  #   ('Contact', 'pages/contact.html')
]

# Base url
# SITE_URL = 'https://www.example.com/' 
SITE_URL = ''

# Base url for static
# STATIC_URL = SITE_URL + 'static/generator'
STATIC_URL = ''

# Base url for pad writing interface, used in debug page
# PAD_BASE_URL = 'https://ethertoff.example.com/w/'
PAD_BASE_URL = ''

DEFAULT_CONTENT_TYPE = 'pad'
SHOW_LOG_MESSAGES = True
SHOW_DEBUG_MESSAGES = True

FIELD_DATE_FORMATS = ['%d.%m.%Y', '%d-%m-%Y', '%d %m %Y', '%d/%m/%Y', '%d %b %Y', '%d %B %Y']
FIELD_TIME_FORMAT = '%H:%M'

TIME_OUTPUT_FORMAT = '%H:%M'
DATE_OUTPUT_FORMAT = '%-d %b %Y'

DATE_OUTPUT_FORMAT_DATE = '%-d'
DATE_OUTPUT_FORMAT_MONTH = '%b'
DATE_OUTPUT_FORMAT_YEAR = '%Y'

# These tags are kept in summary fields
SUMMARY_FIELD_ALLOWED_TAGS = ['em', 'i', 'strong', 'b']

# These tags are completey removed or dropped from summary fields
SUMMARY_FIELD_TAGS_TO_DROP = ['figure', 'h1', 'h2', 'h3', 'h5', 'h6', 'style', 'script']

SYSTEM_PADS = [
    'Labels.md',
    'print.css',
    'generated.css'
]

try:
    LOCAL_SETTINGS
except NameError:
    try:
        from .local_settings import *
    except ImportError:
        pass
