from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
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

def get_chrome_driver():
    """Chrome WebDriver 설정 (WebDriver Manager 사용)"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 백그라운드 실행
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # macOS에서 Chrome 경로 지정
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser'
    ]
    
    chrome_binary = None
    for path in chrome_paths:
        import os
        if os.path.exists(path):
            chrome_binary = path
            break
    
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        logger.info(f"Chrome 바이너리 찾음: {chrome_binary}")
    else:
        logger.warning("Chrome 바이너리를 찾을 수 없음. 시스템 기본값 사용")
    
    try:
        # WebDriver Manager를 사용하여 자동으로 ChromeDriver 다운로드 및 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Chrome WebDriver 생성 실패: {str(e)}")
        raise

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
    """특정 게시판의 공지사항을 크롤링 (Selenium 사용)"""
    new_notices_count = 0
    page = 1
    cutoff_date = timezone.now().date() - timedelta(days=days_back)
    driver = None

    try:
        driver = get_chrome_driver()
        
        while True:
            # 페이지 URL 생성
            page_url = board.url if page == 1 else f"{board.url}?page={page}"
            
            try:
                logger.info(f"{board.name} 페이지 {page} 크롤링 시작: {page_url}")
                
                # 요청 간 지연 시간 추가 (서버 부하 방지)
                import time
                time.sleep(2)  # 2초 대기
                
                driver.get(page_url)
                
                # 페이지 로딩 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                # HTML 소스 가져오기
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, 'html.parser')
                
                # 공지사항 행 찾기
                notice_rows = soup.select('tr:not(.notice)')  # 고정 공지 제외
                
                if not notice_rows:
                    logger.info(f"{board.name} 페이지 {page}: 공지사항이 없음")
                    break
                
                stop_crawling = False
                processed_count = 0
                
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
                        logger.warning(f"날짜 파싱 실패: {date_str}")
                        continue
                    
                    # 오래된 공지사항이면 중단
                    if notice_date < cutoff_date:
                        stop_crawling = True
                        break
                    
                    # 공지사항 저장 (제목만 저장, 원문은 링크로 연결)
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
                        logger.info(f"새 공지사항 저장: {title[:50]}...")
                    
                    processed_count += 1
                
                logger.info(f"{board.name} 페이지 {page}: {processed_count}개 처리, {new_notices_count}개 새로 저장")
                
                if stop_crawling:
                    break
                
                page += 1
                
                # 페이지당 최대 5페이지까지만 (과도한 크롤링 방지)
                if page > 5:
                    logger.info(f"{board.name}: 최대 페이지 수 도달, 크롤링 중단")
                    break
                
            except TimeoutException:
                logger.error(f"{board.name} 페이지 {page}: 페이지 로딩 타임아웃")
                break
            except Exception as e:
                logger.error(f"{board.name} 페이지 {page} 크롤링 오류: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"{board.name} 크롤링 전체 실패: {str(e)}")
    finally:
        if driver:
            driver.quit()
    
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
