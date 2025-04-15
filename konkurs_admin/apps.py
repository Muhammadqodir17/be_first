from django.apps import AppConfig


class KonkursAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konkurs_admin'

    def ready(self):
        from . import signals