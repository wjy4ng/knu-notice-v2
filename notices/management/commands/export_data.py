from django.core.management.base import BaseCommand
from django.utils import timezone
import json
from notices.models import Notice

class Command(BaseCommand):
    help = 'Export crawled data as JSON for GitHub Actions'

    def handle(self, *args, **options):
        """크롤링된 데이터를 JSON으로 내보내기"""
        
        # 최근 공지사항들 가져오기
        notices = Notice.objects.select_related('category', 'board').all().order_by('-created_at')[:200]
        
        data = {
            'notices': [],
            'timestamp': str(timezone.now()),
            'count': notices.count()
        }
        
        for notice in notices:
            data['notices'].append({
                'title': notice.title,
                'url': notice.url,
                'date': notice.date.isoformat() if notice.date else None,
                'category_name': notice.category.name,
                'board_name': notice.board.name,
                'display_order': notice.display_order,
                'created_at': notice.created_at.isoformat(),
            })
        
        # JSON 파일로 저장
        with open('crawled_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {len(data["notices"])} notices to crawled_data.json')
        )
