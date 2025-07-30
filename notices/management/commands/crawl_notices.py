import json
from django.core.management.base import BaseCommand
from django.db import connection
from notices.src.tasks import setup_initial_data, crawl_board_notices
from notices.src.crawler import crawl_notices
from notices.models import NoticeBoard

class Command(BaseCommand):
    help = 'Crawl notices from Kongju University website'

    def handle(self, *args, **options):
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
            boards = NoticeBoard.objects.filter(is_active=True)
            total_new_notices = 0
            all_notices = []

            # 각 게시판을 순회하면서 크롤링
            for board in boards:
                try:
                    new_count = crawl_board_notices(board)
                    total_new_notices += new_count
                    self.stdout.write(f'{board.name}: {new_count}개 새 공지사항 추가')
                    
                    # 크롤링된 데이터를 all_notices 리스트에 추가
                    notices = crawl_notices(board_name=board.name)
                    all_notices.extend(notices)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'{board.name} 크롤링 실패: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully crawled {total_new_notices} new notices')
            )

            # 크롤링된 데이터를 JSON으로 내보내기
            with open('crawled_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_notices, f, ensure_ascii=False, indent=4)
            
            self.stdout.write(self.style.SUCCESS('Successfully crawled and exported data to JSON'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to crawl notices: {e}')
            )