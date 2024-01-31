from django.contrib.auth.models import Group
from etherpadlite.models import PadServer

# @FIXME Come up with better logic for these actions
# show them in the form creation interface?
# Or add them to the settings?

def get_default_pad_server ():
    return PadServer.objects.get(title="etherpad")

# Come up with better logic here?
def get_default_user_group ():
    return Group.objects.get(name="etherpad")