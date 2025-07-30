from django.core.management.base import BaseCommand
from django.db import connection
from notices.src.tasks import crawl_all_notices, setup_initial_data

class Command(BaseCommand):
    help = 'Setup initial data and crawl notices'

    def handle(self, *args, **options):
        # 데이터베이스 연결 및 테이블 확인
        self.stdout.write('Checking database connection...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'Available tables: {tables}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Database connection failed: {e}')
            )
            return

        self.stdout.write('Setting up initial data...')
        try:
            result = setup_initial_data()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully setup initial data: {result}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to setup initial data: {e}')
            )
            return

        self.stdout.write('Starting to crawl notices...')
        try:
            # Celery 없이 직접 함수 호출
            from notices.src.tasks import crawl_board_notices
            from notices.models import NoticeBoard
            
            boards = NoticeBoard.objects.filter(is_active=True)
            total_new_notices = 0
            
            for board in boards:
                try:
                    new_count = crawl_board_notices(board)
                    total_new_notices += new_count
                    self.stdout.write(f'{board.name}: {new_count}개 새 공지사항 추가')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'{board.name} 크롤링 실패: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully crawled {total_new_notices} new notices')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to crawl notices: {e}')
            )
