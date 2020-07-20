from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class GamesConfig(AppConfig):
    name = 'games'

    def ready(self):
        from . import signals


# class MyAdminConfig(AdminConfig):
    # default_site = 'games.admin.MyAdminSite'
