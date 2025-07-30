import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from notices.src.tasks import CATEGORIES  # CATEGORIES import

logger = logging.getLogger(__name__)

def crawl_notices(board_name=None):
    """
    공주대학교 공지사항을 크롤링하는 함수
    """
    base_url = "https://www.kongju.ac.kr/board/bbs/board.do"
    
    all_notices = []
    
    # 특정 게시판만 크롤링할 경우
    if board_name:
        # CATEGORIES에 정의된 게시판인지 확인
        board_data = None
        for category in CATEGORIES:
            for board in category['boards']:
                if board['name'] == board_name:
                    board_data = board
                    break
            if board_data:
                break
        
        if board_data:
            board_url = board_data['url']
            try:
                response = requests.get(board_url)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
                soup = BeautifulSoup(response.content, 'html.parser')
                
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
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Error crawling board {board_url}: {e}")
        else:
            logger.warning(f"Board {board_name} not found in CATEGORIES")
    
    return all_notices