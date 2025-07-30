from django.utils import timezone
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from .models import NoticeCategory, NoticeBoard, Notice

logger = logging.getLogger(__name__)

def crawl_all_notices():
    """모든 게시판의 공지사항을 크롤링"""
    logger.info("=== 크롤링 시작 ===")
    
    # 초기 데이터 설정
    setup_initial_data()
    
    boards = NoticeBoard.objects.filter(is_active=True)
    total_new_notices = 0
    
    for board in boards:
        try:
            new_count = crawl_board_notices(board)
            total_new_notices += new_count
            logger.info(f"{board.name}: {new_count}개 새 공지사항 추가")
        except Exception as e:
            logger.error(f"Failed to crawl {board.name}: {str(e)}")
    
    logger.info(f"=== 크롤링 완료: 총 {total_new_notices}개 수집 ===")
    return total_new_notices

def get_chrome_driver():
    """Chrome WebDriver 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # GitHub Actions 환경
    if os.getenv('GITHUB_ACTIONS'):
        chrome_options.binary_location = '/usr/bin/google-chrome'
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def crawl_board_notices(board, days_back=7):
    """특정 게시판의 공지사항을 크롤링"""
    new_notices_count = 0
    cutoff_date = timezone.now().date() - timedelta(days=days_back)
    driver = None

    try:
        driver = get_chrome_driver()
        
        for page in range(1, 6):  # 최대 5페이지
            page_url = board.url if page == 1 else f"{board.url}?page={page}"
            
            try:
                driver.get(page_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                notice_rows = soup.select('tr:not(.notice)')
                
                if not notice_rows:
                    break
                
                stop_crawling = False
                for index, row in enumerate(notice_rows):
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
                    
                    if notice_date < cutoff_date:
                        stop_crawling = True
                        break
                    
                    # 공지사항 정보 추출
                    title = title_element.get_text(strip=True)
                    url = title_element.get('href', '')
                    if url.startswith('/'):
                        url = 'https://www.kongju.ac.kr' + url
                    
                    # 중복 확인 후 저장
                    notice, created = Notice.objects.get_or_create(
                        board=board,
                        url=url,
                        defaults={
                            'title': title,
                            'published_date': notice_date,
                            'display_order': (page - 1) * 100 + index,
                        }
                    )
                    
                    if created:
                        new_notices_count += 1
                
                if stop_crawling:
                    break
                    
            except TimeoutException:
                logger.warning(f"Timeout on page {page}")
                break
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    finally:
        if driver:
            driver.quit()
    
    return new_notices_count

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
        category, _ = NoticeCategory.objects.get_or_create(name=category_data['name'])
        for board_data in category_data['boards']:
            NoticeBoard.objects.get_or_create(
                category=category,
                name=board_data['name'],
                url=board_data['url'],
            )
