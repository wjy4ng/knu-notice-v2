import requests
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.shortcuts import render

CATEGORIES = [
    {
        'name': '공지사항',
        'boards': [
            {
                'name': '학생소식',
                'url': 'https://www.kongju.ac.kr/KNU/16909/subview.do',
            },
            {
                'name': '행정소식',
                'url': 'https://www.kongju.ac.kr/KNU/16910/subview.do',
            },
            {
                'name': '행사안내',
                'url': 'https://www.kongju.ac.kr/KNU/16911/subview.do',
            },
            {
                'name': '채용소식',
                'url': 'https://www.kongju.ac.kr/KNU/16917/subview.do',
            },
        ],
    },
    {
        'name': '곰나루광장',
        'boards': [
            {
                'name': '열린광장',
                'url': 'https://www.kongju.ac.kr/KNU/16921/subview.do',
            },
            {
                'name': '신문방송사',
                'url': 'https://www.kongju.ac.kr/KNU/16922/subview.do',
            },
            {
                'name': '스터디/모임',
                'url': 'https://www.kongju.ac.kr/KNU/16923/subview.do',
            },
            {
                'name': '분실물센터',
                'url': 'https://www.kongju.ac.kr/KNU/16924/subview.do',
            },
            {
                'name': '사고팔고',
                'url': 'https://www.kongju.ac.kr/KNU/16925/subview.do',
            },
            {
                'name': '자취하숙',
                'url': 'https://www.kongju.ac.kr/KNU/16926/subview.do',
            },
            {
                'name': '아르바이트',
                'url': 'https://www.kongju.ac.kr/KNU/16927/subview.do',
            },
        ],
    },
]

# Create your views here.
def index(req):
    today = datetime.now().strftime('%Y-%m-%d')
    past_date = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
    context = {
        'today': today,
        'past_date': past_date
    }
    return render(req, 'index.html', context)

def proxy_view(req):
    pass

def get_notice_count(req):
    pass

