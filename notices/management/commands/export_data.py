from django.core.management.base import BaseCommand
from django.utils import timezone
import json
from notices.models import Notice

class Command(BaseCommand):
    help = 'Export crawled data as JSON for GitHub Actions'

    def handle(self, *args, **options):
        """크롤링된 데이터를 JSON으로 내보내기"""
        
                # 최신 200개 공지사항 가져오기
        notices = Notice.objects.select_related('category', 'board').all().order_by('-crawled_at')[:200]
        
        data = {
            'notices': [],
            'timestamp': str(timezone.now()),
            'count': notices.count()
        }
        
        for notice in notices:
            data['notices'].append({
                'title': notice.title,
                'url': notice.url,
                'date': notice.published_date.isoformat() if notice.published_date else None,
                'category_name': notice.board.category.name,
                'board_name': notice.board.name,
                'view_count': notice.view_count,
                'is_important': notice.is_important,
                'display_order': notice.display_order,
                'crawled_at': notice.crawled_at.isoformat(),
                'updated_at': notice.updated_at.isoformat(),
            })
        
        # JSON 파일로 저장
        with open('crawled_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {len(data["notices"])} notices to crawled_data.json')
        )
