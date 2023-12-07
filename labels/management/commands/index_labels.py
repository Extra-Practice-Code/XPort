from typing import Any, Optional
from django.core.management.base import BaseCommand
from labels.utils import index_labels

class Command (BaseCommand):
    args = ''
    help = 'Index tags, by reading a pad.'

    def handle(self, *args: Any, **options: Any) -> None:
        index_labels()