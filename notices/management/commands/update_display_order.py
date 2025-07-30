from django.core.management.base import BaseCommand
from notices.models import Notice


class Command(BaseCommand):
    help = 'Update display_order for existing notices'

    def handle(self, *args, **options):
        """기존 공지사항들의 display_order를 설정"""
        notices = Notice.objects.filter(display_order=0).order_by('published_date', 'crawled_at')
        
        count = 0
        for notice in notices:
            # 같은 게시판, 같은 날짜의 공지사항들을 크롤링 시간 순으로 정렬
            same_date_notices = Notice.objects.filter(
                board=notice.board,
                published_date=notice.published_date,
                display_order=0
            ).order_by('crawled_at')
            
            for index, same_notice in enumerate(same_date_notices):
                same_notice.display_order = index
                same_notice.save()
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated display_order for {count} notices')
        )
