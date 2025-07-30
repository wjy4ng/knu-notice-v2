import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import json
import ssl

logger = logging.getLogger(__name__)

def crawl_notices(board_name=None):
    """
    공주대학교 공지사항을 크롤링하는 함수
    """
    base_url = "https://www.kongju.ac.kr/board/bbs/board.do"
    
    all_notices = []
    
    # URL 정보 파일 읽어오기
    with open('notices/src/urls.json', 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
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
                # SSL 프로토콜 버전 명시적으로 지정
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.minimum_version = ssl.TLSVersion.TLSv1_2  # TLS 1.2로 명시적 지정
                
                session = requests.Session()
                session.mount('https://', SSLAdapter(context))
                
                response = session.get(board_url, verify=True)
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
            except Exception as e:
                logger.error(f"알 수 없는 오류 발생: {e}")
        else:
            logger.warning(f"Board {board_name} not found in urls.json")
    
    return all_notices

# requests Session에 SSL Context 적용을 위한 Adapter 클래스
class SSLAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = requests.packages.urllib3.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context)