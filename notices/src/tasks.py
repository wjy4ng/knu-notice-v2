from celery import shared_task
from django.utils import timezone
from notices.models import Notice, NoticeBoard, NoticeCategory
from notices.src.crawler import crawl_notices
import logging

logger = logging.getLogger(__name__)

def setup_initial_data():
    """
    초기 데이터 설정: NoticeCategory, NoticeBoard
    """
    categories = [
        {"name": "학생소식", "is_active": True},
        {"name": "행정소식", "is_active": True},
        {"name": "행사안내", "is_active": True},
        {"name": "채용소식", "is_active": True},
        {"name": "열린광장", "is_active": True},
        {"name": "신문방송사", "is_active": True},
        {"name": "스터디/모임", "is_active": True},
        {"name": "분실물센터", "is_active": True},
        {"name": "사고팔고", "is_active": True},
        {"name": "자취하숙", "is_active": True},
        {"name": "아르바이트", "is_active": True},
    ]

    boards = [
        {"category_name": "학생소식", "name": "학생", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=61&menuNix=496"},
        {"category_name": "학생소식", "name": "학사", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=62&menuNix=496"},
        {"category_name": "학생소식", "name": "장학", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=63&menuNix=496"},
        {"category_name": "학생소식", "name": "모집", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=64&menuNix=496"},
        {"category_name": "학생소식", "name": "교환학생", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=344&menuNix=496"},
        {"category_name": "학생소식", "name": "기타", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=65&menuNix=496"},
        {"category_name": "행정소식", "name": "일반", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=58&menuNix=495"},
        {"category_name": "행정소식", "name": "학사", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=59&menuNix=495"},
        {"category_name": "행정소식", "name": "장학", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=60&menuNix=495"},
        {"category_name": "행사안내", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=57&menuNix=494"},
        {"category_name": "채용소식", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=66&menuNix=497"},
        {"category_name": "열린광장", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=67&menuNix=498"},
        {"category_name": "신문방송사", "name": "보도", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=68&menuNix=499"},
        {"category_name": "스터디/모임", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=69&menuNix=500"},
        {"category_name": "분실물센터", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=70&menuNix=501"},
        {"category_name": "사고팔고", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=71&menuNix=502"},
        {"category_name": "자취하숙", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=72&menuNix=503"},
        {"category_name": "아르바이트", "name": "전체", "url": "https://www.kongju.ac.kr/board/bbs/board.do?bsIdx=73&menuNix=504"},
    ]

    created_count = 0
    for category_data in categories:
        category, created = NoticeCategory.objects.get_or_create(
            name=category_data['name'],
            defaults={'is_active': category_data['is_active']}
        )
        if created:
            created_count += 1

    for board_data in boards:
        category = NoticeCategory.objects.get(name=board_data['category_name'])
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