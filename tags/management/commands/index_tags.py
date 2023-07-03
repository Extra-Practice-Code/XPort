from typing import Any, Optional
from django.core.management.base import BaseCommand
from tags.utils import index_tags

class Command (BaseCommand):
    args = ''
    help = 'Index tags, by reading a pad.'

    def handle(self, *args: Any, **options: Any) -> None:
        index_tags()