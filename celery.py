import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knu_notice.settings')

app = Celery('knu_notice')