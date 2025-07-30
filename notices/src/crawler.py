from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

def crawl_notices(board_name=None):
    """
    공주대학교 공지사항을 크롤링하는 함수 (Selenium 사용)
    """
    base_url = "https://www.kongju.ac.kr/board/bbs/board.do"
    
    all_notices = []
    
    # URL 정보 파일 읽어오기
    with open('notices/src/urls.json', 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
    # Selenium 옵션 설정
    options = Options()
    options.add_argument("--headless")  # Headless 모드로 실행 (GUI 없이 실행)
    options.add_argument("--disable-gpu")  # GPU 가속 사용 안 함
    options.add_argument("--no-sandbox")  # Sandbox 모드 사용 안 함
    options.add_argument("--disable-dev-shm-usage")  # /dev/shm 공간 공유 안 함
    
    # Chrome WebDriver 실행 (경로 설정 필요)
    driver = webdriver.Chrome(options=options)
    
    try:
        # 특정 게시판만 크롤링할 경우
        if board_name:
            # 게시판 URL 가져오기
            board_url = None
            for category, boards in urls.items():
                if board_name in boards:
                    board_url = boards[board_name]
                    break
            
            if board_url:
                try:
                    driver.get(board_url)
                    
                    # 페이지 소스 가져오기
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 게시물 목록 추출
                    notice_list = soup.select('div.board-list > ul > li')
                    
                    for notice in notice_list:
                        try:
                            # 중요 공지사항
                            is_important = bool(notice.select_one('span.icon-important'))
                            
                            # 게시물 링크
                            link = notice.select_one('a')
                            url = base_url + link['href'] if link and 'href' in link.attrs else None
                            
                            # 게시물 제목
                            title = link.text.strip() if link else None
                            
                            # 게시물 번호
                            num = notice.select_one('td.num').text.strip() if notice.select_one('td.num') else None
                            
                            # 작성일
                            date = notice.select_one('td.date').text.strip() if notice.select_one('td.date') else None
                            
                            # 조회수
                            view_count = notice.select_one('td.view').text.strip() if notice.select_one('td.view') else None
                            
                            # 작성자
                            author = notice.select_one('td.author').text.strip() if notice.select_one('td.author') else None
                            
                            notice_data = {
                                "title": title,
                                "url": url,
                                "is_important": is_important,
                                "num": num,
                                "date": date,
                                "view_count": view_count,
                                "author": author,
                                "board_name": board_name,
                                "category_name": board_name,
                                "crawled_at": datetime.now().isoformat()
                            }
                            
                            all_notices.append(notice_data)
                        
                        except Exception as e:
                            logger.error(f"Error processing notice: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"Error crawling board {board_url}: {e}")
            else:
                logger.warning(f"Board {board_name} not found in urls.json")
    
    finally:
        driver.quit()  # WebDriver 종료
    
    return all_notices