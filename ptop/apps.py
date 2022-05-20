from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PtopConfig(AppConfig):
    name = 'ptop'

    def ready(self):
        from . import signals
        from .models import create_default_site_detail
        post_migrate.connect(create_default_site_detail, sender=self)
