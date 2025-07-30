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

def crawl_all_notices():
    """Main task to crawl notices from all active boards"""
    from django.utils import timezone
    from django.db import transaction
    
    start_time = timezone.now()
    logger.info(f"=== 크롤링 시작: {start_time} ===")
    
    # 초기 데이터 설정
    try:
        setup_initial_data()
    except Exception as e:
        logger.error(f"Failed to setup initial data: {str(e)}")
        return 0
    
    boards = NoticeBoard.objects.filter(is_active=True)
    total_new_notices = 0
    failed_boards = []
    
    for board in boards:
        try:
            with transaction.atomic():  # 각 게시판별로 트랜잭션 분리
                new_count = crawl_board_notices(board)
                total_new_notices += new_count
                logger.info(f"{board.name}: {new_count}개 새 공지사항 추가")
        except Exception as e:
            logger.error(f"Failed to crawl {board.name}: {str(e)}")
            failed_boards.append(board.name)
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"=== 크롤링 완료: {end_time} (소요시간: {duration:.1f}초) ===")
    logger.info(f"총 {total_new_notices}개 새 공지사항 수집")
    
    if failed_boards:
        logger.warning(f"실패한 게시판들: {', '.join(failed_boards)}")
    
    return total_new_notices

def get_chrome_driver():
    """Chrome WebDriver 설정 (GitHub Actions 및 로컬 환경 지원)"""
    import os
    is_github_actions = os.getenv('GITHUB_ACTIONS') is not None
    
    chrome_options = Options()
    
    # 기본 설정
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 최적화 설정
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--disable-javascript')
    
    # 사용자 에이전트
    chrome_options.add_argument('--user-agent=KNU-Notice-Crawler/1.0 (Educational Purpose)')
    
    # Chrome 바이너리 경로 설정
    if is_github_actions:
        # GitHub Actions 환경 (Ubuntu)
        chrome_options.binary_location = '/usr/bin/google-chrome'
        logger.info("Using Chrome binary for GitHub Actions")
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
                driver.get(page_url)
                
                # 페이지 로딩 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 공지사항 목록 추출
                notices = extract_notices_from_page(driver, board, cutoff_date)
                
                if not notices:
                    logger.info(f"No more notices found on page {page}, stopping crawl")
                    break
                
                # 새로운 공지사항만 저장
                page_new_count = 0
                for notice_data in notices:
                    if save_notice_if_new(notice_data, board):
                        page_new_count += 1
                
                new_notices_count += page_new_count
                logger.info(f"Page {page}: {page_new_count} new notices saved")
                
                # 날짜 기준 중단 조건
                if notices and all(notice['date'] < cutoff_date for notice in notices):
                    logger.info(f"Reached cutoff date ({cutoff_date}), stopping crawl")
                    break
                
                page += 1
                
            except TimeoutException:
                logger.warning(f"Timeout loading page {page} for {board.name}")
                break
            except Exception as e:
                logger.error(f"Error crawling page {page} for {board.name}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Failed to initialize driver for {board.name}: {str(e)}")
        raise
    finally:
        # 드라이버 정리
        if driver:
            try:
                driver.quit()
                logger.debug(f"WebDriver closed for {board.name}")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {str(e)}")
    
    return new_notices_count

def extract_notices_from_page(driver, board, cutoff_date):
    """페이지에서 공지사항 목록을 추출"""
    import time
    time.sleep(3)  # 서버 부하 최소화를 위한 대기시간
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        
        notice_rows = soup.select('tr:not(.notice)')
        
        if not notice_rows:
            return []
        
        notices = []
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
            
            title = title_element.get_text(strip=True)
            url = title_element.get('href', '')
            
            if url.startswith('/'):
                url = 'https://www.kongju.ac.kr' + url
            
            notices.append({
                'title': title,
                'url': url,
                'date': notice_date,
                'index': index
            })
        
        return notices
        
    except Exception as e:
        logger.error(f"Error extracting notices from page: {str(e)}")
        return []

def save_notice_if_new(notice_data, board):
    """새로운 공지사항인 경우에만 저장"""
    try:
        # 페이지와 행 위치를 기반으로 표시 순서 계산 (작을수록 최신)
        display_order = notice_data['index']
        
        notice, created = Notice.objects.get_or_create(
            board=board,
            url=notice_data['url'],
            defaults={
                'title': notice_data['title'],
                'published_date': notice_data['date'],
                'author': '',
                'view_count': 0,
                'display_order': display_order,
            }
        )
        
        if created:
            logger.info(f"New notice saved: {notice_data['title'][:50]}...")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error saving notice: {str(e)}")
        return False

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
