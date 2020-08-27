from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'games_ecommerce.settings')

app = Celery('games_ecommerce')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'run-every-30-seconds': {
#         'task': 'games.tasks.delete_unactive_carts',
#         'schedule': 30.0,
#         'args': (),
#     },
# }