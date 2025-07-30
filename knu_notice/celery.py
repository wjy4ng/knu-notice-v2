import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knu_notice.settings')

app = Celery('knu_notice')

# Django 설정 사용
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 태스크 자동 발견
app.autodiscover_tasks()

# 주기적 태스크 설정
app.conf.beat_schedule = {
    'crawl-notices-every-hour': {
        'task': 'notices.tasks.crawl_all_notices',
        'schedule': 3600.0,  # 1시간마다 실행
    },
}

app.conf.timezone = 'Asia/Seoul'