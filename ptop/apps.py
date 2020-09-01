from django.apps import AppConfig


class PtopConfig(AppConfig):
    name = 'ptop'

    def ready(self):
        from . import signals
