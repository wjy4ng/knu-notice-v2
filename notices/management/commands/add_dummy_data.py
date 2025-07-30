from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from notices.models import NoticeCategory, NoticeBoard, Notice

class Command(BaseCommand):
    help = 'Add dummy notice data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Adding dummy notice data...')
        
        try:
            # 더미 공지사항 데이터 생성 (최근 7일간)
            today = datetime.now().date()
            
            boards = NoticeBoard.objects.all()
            
            dummy_notices = [
                "2025학년도 1학기 기말고사 일정 안내",
                "학생증 재발급 신청 안내", 
                "도서관 운영시간 변경 공지",
                "장학금 신청 기간 연장 안내",
                "캠퍼스 공사 관련 안내사항",
                "학생식당 메뉴 변경 공지",
                "온라인 수업 시스템 점검 안내",
                "졸업논문 제출 일정 공지",
            ]
            
            total_created = 0
            
            for board in boards:
                for i, title in enumerate(dummy_notices):
                    # 최근 7일 중 다양한 날짜로 생성
                    days_ago = i % 7  # 0~6일 전
                    notice_date = today - timedelta(days=days_ago)
                    
                    notice, created = Notice.objects.get_or_create(
                        board=board,
                        title=f"[{board.name}] {title}",
                        published_date=notice_date,
                        defaults={
                            'url': f'https://www.kongju.ac.kr/dummy/{board.id}/{i}',
                            'author': '관리자',
                            'view_count': i * 10,
                        }
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(f'Created: {notice.title}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {total_created} dummy notices')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create dummy data: {e}')
            )
