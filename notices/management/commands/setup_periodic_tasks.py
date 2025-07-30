from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Setup periodic tasks for notice crawling'

    def handle(self, *args, **options):
        # Create interval schedule (every 1 hour)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        # Create periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name='Crawl All Notices',
            defaults={
                'task': 'notices.tasks.crawl_all_notices',
                'interval': schedule,
                'enabled': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created periodic task: Crawl All Notices')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Periodic task already exists: Crawl All Notices')
            )
