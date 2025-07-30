from celery import shared_task
from django.utils import timezone
from notices.models import Notice, NoticeBoard, NoticeCategory
from notices.src.crawler import crawl_notices
import logging
import json

logger = logging.getLogger(__name__)

def setup_initial_data():
    """
    초기 데이터 설정: NoticeCategory, NoticeBoard
    """
    # URL 정보 파일 읽어오기
    with open('notices/src/urls.json', 'r', encoding='utf-8') as f:
        urls = json.load(f)

    created_count = 0
    for category_name, boards in urls.items():
        category, created = NoticeCategory.objects.get_or_create(
            name=category_name,
        )
        if created:
            created_count += 1
        for board_name, board_url in boards.items():
            board, created = NoticeBoard.objects.get_or_create(
                category=category,
                name=board_name,
                defaults={
                    'url': board_url,
                    'is_active': True
                }
            )
            if created:
                created_count += 1

    return created_count

def crawl_board_notices(board):
    """
    특정 게시판의 공지사항을 크롤링하는 함수
    """
    new_notices_count = 0
    try:
        notices = crawl_notices(board_name=board.name)
        for notice in notices:
            # 공지사항이 이미 존재하는지 확인
            if not Notice.objects.filter(title=notice['title'], url=notice['url']).exists():
                # 존재하지 않으면 새로운 공지사항 생성
                Notice.objects.create(
                    board=board,
                    title=notice['title'],
                    url=notice['url'],
                    published_date=notice['date'],
                    display_order=notice['display_order'],
                )
                new_notices_count += 1
    except Exception as e:
        logger.error(f"{board.name} 크롤링 중 오류 발생: {e}")
    return new_notices_count