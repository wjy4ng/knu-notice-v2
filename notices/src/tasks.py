from celery import shared_task
from django.utils import timezone
from notices.models import Notice, NoticeBoard, NoticeCategory
from notices.src.crawler import crawl_notices
import logging

logger = logging.getLogger(__name__)

def get_board_url(board_name):
    """
    게시판 이름으로 게시판 URL을 반환하는 함수
    """
    for category in CATEGORIES:
        for board in category['boards']:
            if board['name'] == board_name:
                return board['url']
    return None

def setup_initial_data():
    """
    초기 데이터 설정: NoticeCategory, NoticeBoard
    """
    CATEGORIES = [
        {
            "name": "공지사항",
            "boards": [
                {
                    "name": "학생소식",
                    "url": "https://www.kongju.ac.kr/KNU/16909/subview.do",
                },
                {
                    "name": "행정소식",
                    "url": "https://www.kongju.ac.kr/KNU/16910/subview.do",
                },
                {
                    "name": "행사안내",
                    "url": "https://www.kongju.ac.kr/KNU/16911/subview.do",
                },
                {
                    "name": "채용소식",
                    "url": "https://www.kongju.ac.kr/KNU/16917/subview.do",
                },
            ],
        },
        {
            "name": "곰나루광장",
            "boards": [
                {
                    "name": "열린광장",
                    "url": "https://www.kongju.ac.kr/KNU/16921/subview.do",
                },
                {
                    "name": "신문방송사",
                    "url": "https://www.kongju.ac.kr/KNU/16922/subview.do",
                },
                {
                    "name": "스터디/모임",
                    "url": "https://www.kongju.ac.kr/KNU/16923/subview.do",
                },
                {
                    "name": "분실물센터",
                    "url": "https://www.kongju.ac.kr/KNU/16924/subview.do",
                },
                {
                    "name": "사고팔고",
                    "url": "https://www.kongju.ac.kr/KNU/16925/subview.do",
                },
                {
                    "name": "자취하숙",
                    "url": "https://www.kongju.ac.kr/KNU/16926/subview.do",
                },
                {
                    "name": "아르바이트",
                    "url": "https://www.kongju.ac.kr/KNU/16927/subview.do",
                },
            ],
        },
    ]

    created_count = 0
    for category_data in CATEGORIES:
        category, created = NoticeCategory.objects.get_or_create(
            name=category_data['name'],
        )
        if created:
            created_count += 1
        for board_data in category_data['boards']:
            board, created = NoticeBoard.objects.get_or_create(
                category=category,
                name=board_data['name'],
                defaults={
                    'url': board_data['url'],
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