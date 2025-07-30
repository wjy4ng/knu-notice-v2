# Celery 가져오기 (선택적)
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Celery가 없을 때 사용할 더미 데코레이터
    def shared_task(func):
        return func

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
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from .models import NoticeCategory, NoticeBoard, Notice

logger = logging.getLogger(__name__)

@shared_task
def crawl_all_notices():
    """Main task to crawl notices from all active boards"""
    from django.utils import timezone
    
    start_time = timezone.now()
    logger.info(f"=== 크롤링 시작: {start_time} ===")
    
    boards = NoticeBoard.objects.filter(is_active=True)
    total_new_notices = 0
    
    for board in boards:
        try:
            new_count = crawl_board_notices(board)
            total_new_notices += new_count
            logger.info(f"{board.name}: {new_count} new notices added")
        except Exception as e:
            logger.error(f"Failed to crawl {board.name}: {str(e)}")
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"=== 크롤링 완료: {end_time} (소요시간: {duration:.1f}초) ===")
    logger.info(f"총 {total_new_notices}개 새 공지사항 수집")
    
    return total_new_notices

def get_chrome_driver():
    """Chrome WebDriver 설정 (GitHub Actions 및 로컬 환경 지원)"""
    # 환경 확인
    import os
    is_render = os.getenv('RENDER') is not None
    is_github_actions = os.getenv('GITHUB_ACTIONS') is not None
    
    if is_render:
        # Render.com 환경에서는 Chrome이 설치되지 않으므로 크롤링 비활성화
        logger.warning("크롤링이 Render.com 환경에서 비활성화됨. GitHub Actions를 사용하세요.")
        raise WebDriverException("크롤링은 GitHub Actions에서만 실행됩니다.")
    
    chrome_options = Options()
    
    # 기본 보안 설정
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 보안 강화 설정
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 향상
    chrome_options.add_argument('--disable-javascript')  # JS 비활성화 (보안)
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    
    # 사용자 에이전트 (공주대학교 크롤링 명시)
    chrome_options.add_argument('--user-agent=KNU-Notice-Crawler/1.0 (Educational Purpose)')
    
    is_debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    if is_debug:
        # 로컬 개발환경에서만 SSL 무시
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
    
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Chrome 바이너리 경로 설정
    if is_github_actions:
        # GitHub Actions 환경 (Ubuntu)
        chrome_options.binary_location = '/usr/bin/google-chrome'
        logger.info("Using Chrome binary for GitHub Actions: /usr/bin/google-chrome")
    else:
        # 로컬 환경 (macOS)
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser'
    ]
    
    chrome_binary = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_binary = path
            break
    
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        logger.info(f"Chrome binary found: {chrome_binary}")
    else:
        logger.warning("Chrome binary not found, using system default")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Failed to create Chrome WebDriver: {str(e)}")
        raise

def crawl_board_notices(board, days_back=7):
    """특정 게시판의 공지사항을 크롤링 (Selenium 사용)"""
    new_notices_count = 0
    page = 1
    cutoff_date = timezone.now().date() - timedelta(days=days_back)
    driver = None

    try:
        driver = get_chrome_driver()
        
        while page <= 5:  # 최대 5페이지까지
            page_url = board.url if page == 1 else f"{board.url}?page={page}"
            
            try:
                logger.info(f"Crawling {board.name} page {page}: {page_url}")
                
                import time
                time.sleep(3)  # 서버 부하 최소화를 위한 대기시간 증가
                
                driver.get(page_url)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, 'html.parser')
                
                notice_rows = soup.select('tr:not(.notice)')
                
                if not notice_rows:
                    logger.info(f"{board.name} page {page}: No notices found")
                    break
                
                stop_crawling = False
                processed_count = 0
                
                for index, row in enumerate(notice_rows):
                    date_cell = row.select_one('.td-date')
                    title_element = row.select_one('td a')
                    
                    if not date_cell or not title_element:
                        continue
                    
                    date_str = date_cell.get_text(strip=True).replace('.', '-')
                    try:
                        notice_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        logger.warning(f"Date parsing failed: {date_str}")
                        continue
                    
                    if notice_date < cutoff_date:
                        stop_crawling = True
                        break
                    
                    title = title_element.get_text(strip=True)
                    url = title_element.get('href', '')
                    
                    if url.startswith('/'):
                        url = 'https://www.kongju.ac.kr' + url
                    
                    # 페이지와 행 위치를 기반으로 표시 순서 계산 (작을수록 최신)
                    display_order = (page - 1) * 100 + index
                    
                    notice, created = Notice.objects.get_or_create(
                        board=board,
                        url=url,
                        defaults={
                            'title': title,
                            'published_date': notice_date,
                            'author': '',
                            'view_count': 0,
                            'display_order': display_order,
                        }
                    )
                    
                    if created:
                        new_notices_count += 1
                        logger.info(f"New notice saved: {title[:50]}...")
                    
                    processed_count += 1
                
                logger.info(f"{board.name} page {page}: {processed_count} processed, {new_notices_count} new")
                
                if stop_crawling:
                    break
                    
                page += 1
                
            except TimeoutException:
                logger.error(f"{board.name} page {page}: Page loading timeout")
                break
            except Exception as e:
                logger.error(f"Error processing {board.name} page {page}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Critical error in crawl_board_notices for {board.name}: {str(e)}")
    finally:
        if driver:
            driver.quit()
    
    return new_notices_count

@shared_task
def setup_initial_data():
    """Setup initial category and board data"""
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
    return "Initial data setup completed"
