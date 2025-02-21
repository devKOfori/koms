import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "koms.settings")

app = Celery("koms")

# Load task modules from all registered Django apps
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from apps
app.autodiscover_tasks()
