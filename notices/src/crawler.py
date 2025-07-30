import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def crawl_notices(board_name=None):
    """
    공주대학교 공지사항을 크롤링하는 함수
    """
    base_url = "https://www.kongju.ac.kr/board/bbs/board.do"
    
    # 크롤링할 게시판 목록 (board_name이 지정되지 않았을 경우)
    if not board_name:
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
    else:
        # 특정 게시판만 크롤링할 경우
        boards = [board for board in boards if board['name'] == board_name]
    
    all_notices = []
    
    for board in boards:
        board_url = board['url']
        
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
                        "board_name": board['name'],
                        "category_name": board['category_name'],
                        "crawled_at": datetime.now().isoformat()
                    }
                    
                    all_notices.append(notice_data)
                
                except Exception as e:
                    logger.error(f"Error processing notice: {e}")
                    continue
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error crawling board {board_url}: {e}")
            continue
    
    return all_notices