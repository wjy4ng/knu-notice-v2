import requests
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta
from django.shortcuts import render
from .models import NoticeCategory, Notice, NoticeBoard

def index(req):
    today = datetime.now().strftime('%Y-%m-%d')
    past_date = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
    context = {
        'today': today,
        'past_date': past_date
    }
    return render(req, 'index.html', context)

def get_notice_count(req):
    """날짜별 모든 게시판의 공지사항 개수를 반환하는 API"""
    date_str = req.GET.get('date')
    if not date_str:
        return JsonResponse({'error': '날짜가 필요합니다'}, status=400)
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '잘못된 날짜 형식입니다.'}, status=400)
    
    categories_data = []
    for category in NoticeCategory.objects.all():
        boards_data = []
        for board in category.boards.filter(is_active=True):
            notice_count = Notice.objects.filter(
                board=board,
                published_date=target_date
            ).count()

            boards_data.append({
                'name': board.name,
                'url': board.url,
                'count': notice_count
            })

        categories_data.append({
            'name': category.name,
            'boards': boards_data
        })
    return JsonResponse({'categories': categories_data})

def get_notice_preview(req):
    """특정 게시판의 공지사항 미리보기를 반환하는 API"""
    board_url = req.GET.get('url')
    date_str = req.GET.get('date')

    if not board_url or not date_str:
        return JsonResponse({'error': 'URL과 날짜가 필요합니다'}, status=400)
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        board = NoticeBoard.objects.get(url=board_url)
    except (ValueError, NoticeBoard.DoesNotExist):
        return JsonResponse({'error': '잘못된 요청입니다'}, status=400)
    
    # 해당 날짜의 공지사항 가져오기
    notices = Notice.objects.filter(
        board=board,
        published_date=target_date
    ).order_by('-crawled_at')[:5]

    notices_data = [
        {
            'title': notice.title,
            'url': notice.url
        }
        for notice in notices
    ]

    return JsonResponse({
        'board_name': board.name,
        'notices': notices_data,
        'count': len(notices_data)
    })

def proxy_view(req):
    """기존 proxy.js 기능을 Django로 구현"""
    url = req.GET.get('url')
    if not url:
        return HttpResponse('URL이 필요합니다', status=400)        
    try:
        res = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return HttpResponse(res.text, content_type='text/html')
    except Exception as e:
        return HttpResponse(f'요청 실패: {str(e)}', status=500)