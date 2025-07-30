import requests
import json
import os
from django.core.management.base import BaseCommand
from notices.models import Notice

class Command(BaseCommand):
    help = 'Send crawled data to Render.com'

    def handle(self, *args, **options):
        """크롤링된 데이터를 Render.com으로 전송"""
        
        # 최근 100개 공지사항 가져오기
        notices = Notice.objects.all().order_by('-created_at')[:100]
        
        data = []
        for notice in notices:
            data.append({
                'title': notice.title,
                'url': notice.url,
                'date': notice.date.isoformat() if notice.date else None,
                'category': notice.category.name,
                'board': notice.board.name,
                'display_order': notice.display_order,
            })
        
        # Render.com으로 데이터 전송
        render_url = os.getenv('RENDER_APP_URL', 'https://your-app.onrender.com')
        
        try:
            response = requests.post(
                f"{render_url}/api/sync-data/",
                json={'notices': data},
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {os.getenv("CRAWL_AUTH_TOKEN", "knu-crawl-2025")}'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced {len(data)} notices to Render.com')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to sync data: {response.status_code} - {response.text}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing data: {str(e)}')
            )
