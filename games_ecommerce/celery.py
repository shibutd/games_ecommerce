from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'games_ecommerce.settings')

app = Celery('games_ecommerce')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'delete_unactive_carts': {
        'task': 'games.tasks.delete_unactive_carts',
        'schedule': crontab(hour=4, day_of_week='2, 5'),
        'args': (),
    },
}
