import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shashan.settings')

app = Celery('shashan')

# Read config from Django settings, using a CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in all installed apps (like your tasks.py)
app.autodiscover_tasks()