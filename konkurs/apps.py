from django.apps import AppConfig


class KonkursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konkurs'

    def ready(self):
        from . import signals