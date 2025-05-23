from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(worker_concurrency=4)  # Adjust based on CPU power
app.conf.task_acks_late = True  # Ensures tasks are not lost on worker failure