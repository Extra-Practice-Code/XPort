# -*- coding: utf-8 -*-

# Python imports

import os
import urllib

# PyPi imports

from py_etherpad import EtherpadLiteClient

# Django imports

from django.core.management.base import BaseCommand

# Django Apps import

from etherpadlite.models import Pad
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = 'Write all pads to plain text files'

    def handle(self, *args, **options):
        
        for pad in Pad.objects.all():
            padID = pad.group.groupID + '$' + urllib.quote_plus(pad.name.replace('::', '_'))
            epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)
            
            text = epclient.getText(padID)['text']

            backup_file_path = os.path.join(settings.BACKUP_DIR, pad.display_slug)
            
            with open(backup_file_path.encode('utf-8'), 'w') as f:
                f.write(text.encode('utf-8'))
