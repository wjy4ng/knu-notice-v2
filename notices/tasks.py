from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import logging
from .models import NoticeCategory, NoticeBoard, Notice

logger = logging.getLogger(__name__)

@shared_task
def crawl_all_notices():
    """모든 게시판의 공지사항을 크롤링하는 메인 테스크"""
    logger.info("공지사항 크롤링 시작")
    
    boards = NoticeBoard.objects.filter(is_active=True)

    total_new_notices = 0
    for board in boards:
        try:
            new_count = crawl_board_notices(board)
            total_new_notices += new_count
            logger.info(f"{board.name}: {new_count}개 새 공지사항 추가")
        except Exception as e:
            logger.error(f"{board.name} 크롤링 실패: {str(e)}")
    return total_new_notices

def crawl_board_notices(board, days_back=7):
    """특정 게시판의 공지사항을 크롤링"""
    new_notices_count = 0
    page = 1
    cutoff_date = timezone.now().date() - timedelta(days=days_back)

    while True:
        # 페이지 URL 생성
        page_url = board.url if page == 1 else f"{board.url}?page={page}"

        try:
            res = requests.get(page_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'html.parser')
            notice_rows = soup.select('tr:not(.notice)') # 고정 공지 제외
            if not notice_rows:
                break
            stop_crawling = False
            for row in notice_rows:
                date_cell = row.select_one('.td-date')
                title_element = row.select_one('td a')
                if not date_cell or not title_element:
                    continue
                
                # 날짜 파싱
                date_str = date_cell.get_text(strip=True).replace('.', '-')
                try:
                    notice_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
                
                # 오래된 공지사항이면 중단
                if notice_date < cutoff_date:
                    stop_crawling = True
                    break

                # 공지사항 저장
                title = title_element.get_text(strip=True)
                url = title_element.get('href', '')

                # 상대 URL을 절대 URL로 변환
                if url.startswith('/'):
                    url = 'https://www.kongju.ac.kr' + url

                # 중복 체크 후 저장
                notice, created = Notice.objects.get_or_create(
                    board=board,
                    url=url,
                    defaults={
                        'title': title,
                        'published_date': notice_date,
                        'author': '',
                        'view_count': 0,
                    }
                )

                if created:
                    new_notices_count += 1
            if stop_crawling:
                break

            page += 1
        except Exception as e:
            logger.error(f"{board.name} 페이지 {page} 크롤링 오류: {str(e)}")
            break
    return new_notices_count

@shared_task
def setup_initial_data():
    """초기 카테고리와 게시판 데이터 설정"""
    categories_data = [
        {
            'name': '공지사항',
            'boards': [
                {'name': '학생소식', 'url': 'https://www.kongju.ac.kr/KNU/16909/subview.do'},
                {'name': '행정소식', 'url': 'https://www.kongju.ac.kr/KNU/16910/subview.do'},
                {'name': '행사안내', 'url': 'https://www.kongju.ac.kr/KNU/16911/subview.do'},
                {'name': '채용소식', 'url': 'https://www.kongju.ac.kr/KNU/16917/subview.do'},
            ]
        },
        {
            'name': '곰나루광장',
            'boards': [
                {'name': '열린광장', 'url': 'https://www.kongju.ac.kr/KNU/16921/subview.do'},
                {'name': '신문방송사', 'url': 'https://www.kongju.ac.kr/KNU/16922/subview.do'},
                {'name': '스터디/모임', 'url': 'https://www.kongju.ac.kr/KNU/16923/subview.do'},
                {'name': '분실물센터', 'url': 'https://www.kongju.ac.kr/KNU/16924/subview.do'},
                {'name': '사고팔고', 'url': 'https://www.kongju.ac.kr/KNU/16925/subview.do'},
                {'name': '자취하숙', 'url': 'https://www.kongju.ac.kr/KNU/16926/subview.do'},
                {'name': '아르바이트', 'url': 'https://www.kongju.ac.kr/KNU/16927/subview.do'},
            ]
        }
    ]

    for category_data in categories_data:
        category, _ = NoticeCategory.objects.get_or_create(
            name=category_data['name']
        )

        for board_data in category_data['boards']:
            NoticeBoard.objects.get_or_create(
                category=category,
                name=board_data['name'],
                url=board_data['url'],
            )
    return "초기 데이터 설정 완료"
