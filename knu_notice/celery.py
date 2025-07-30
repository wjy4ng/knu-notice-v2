import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knu_notice.settings')

app = Celery('knu_notice')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'crawl-notices-every-hour': {
        'task': 'notices.tasks.crawl_all_notices',
        'schedule': 3600.0,
    }
}

app.conf.timezone = 'Asia/Seoul'