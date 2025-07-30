from django.http import JsonResponse
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

def get_notice_counts(req):
    """날짜별 모든 게시판의 공지사항 개수를 반환하는 API (최적화)"""
    date_str = req.GET.get('date')
    if not date_str:
        return JsonResponse({'error': '날짜가 필요합니다'}, status=400)
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '잘못된 날짜 형식입니다.'}, status=400)
    
    # 데이터베이스 쿼리 최적화: select_related 사용
    categories_data = []
    categories = NoticeCategory.objects.prefetch_related(
        'boards__notices'
    ).all()
    
    for category in categories:
        boards_data = []
        for board in category.boards.filter(is_active=True):
            notice_count = board.notices.filter(
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
    
    # 해당 날짜의 공지사항 가져오기 (웹사이트 표시 순서대로)
    notices = Notice.objects.filter(
        board=board,
        published_date=target_date
    ).order_by('display_order')[:5]  # display_order가 작을수록 위에 표시된 공지

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