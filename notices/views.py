from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def debug_notices(req):
    """DB에 저장된 Notice, NoticeBoard, NoticeCategory의 개수와 일부 샘플 데이터를 반환"""
    from .models import Notice, NoticeBoard, NoticeCategory
    data = {
        'notice_count': Notice.objects.count(),
        'notice_sample': list(Notice.objects.all().order_by('-id').values('id','title','published_date','board__name')[:5]),
        'board_count': NoticeBoard.objects.count(),
        'board_sample': list(NoticeBoard.objects.all().order_by('-id').values('id','name','url')[:5]),
        'category_count': NoticeCategory.objects.count(),
        'category_sample': list(NoticeCategory.objects.all().order_by('-id').values('id','name')[:5]),
    }
    logger.info(f"[DEBUG-NOTICES] {data}")
    return JsonResponse(data)
from django.http import JsonResponse, HttpResponseNotAllowed
from datetime import datetime, timedelta
from django.shortcuts import render
from .models import NoticeCategory, Notice, NoticeBoard
import logging

logger = logging.getLogger(__name__)

def index(req):
    """메인 페이지"""
    today = datetime.now().strftime('%Y-%m-%d')
    past_date = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
    context = {
        'today': today,
        'past_date': past_date
    }
    return render(req, 'index.html', context)

def get_notice_counts(req):
    """날짜별 모든 게시판의 공지사항 개수를 반환 (GET only)"""
    if req.method != 'GET':
        return HttpResponseNotAllowed(['GET']) 

    date_str = req.GET.get('date')
    if not date_str:
        return JsonResponse({'error': '날짜가 필요합니다'}, status=400)
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '잘못된 날짜 형식입니다.'}, status=400)
    except Exception as e:  # 예외 처리 추가
        logger.exception("날짜 처리 중 오류")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
    
    categories_data = []
    categories = NoticeCategory.objects.all()
    
    for category in categories:
        boards_data = []
        for board in category.boards.filter(is_active=True):
            notice_count = board.notices.filter(published_date=target_date).count()
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
    """특정 게시판의 공지사항 미리보기를 반환 (GET only)"""
    if req.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    board_url = req.GET.get('url')
    date_str = req.GET.get('date')
    
    if not board_url or not date_str:
        return JsonResponse({'error': 'URL과 날짜가 필요합니다'}, status=400)
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        board = NoticeBoard.objects.get(url=board_url, is_active=True)
    except ValueError:
        return JsonResponse({'error': '잘못된 날짜 형식입니다.'}, status=400)
    except NoticeBoard.DoesNotExist:
        return JsonResponse({'error': '게시판을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.exception("게시판 조회 중 오류")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
    
    notices = Notice.objects.filter(
        board=board,
        published_date=target_date
    ).order_by('display_order')[:5]
    
    notices_data = [
        {
            'title': notice.title,
            'url': notice.url,
            'author': notice.author,
            'view_count': notice.view_count,
            'is_important': notice.is_important
        } for notice in notices
    ]
    
    return JsonResponse({
        'board_name': board.name,
        'date': date_str,
        'notices': notices_data,
        'total_count': len(notices_data)
    })