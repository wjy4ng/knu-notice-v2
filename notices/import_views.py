from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from notices.models import NoticeCategory, NoticeBoard, Notice
from datetime import datetime
import json
import os

@method_decorator(csrf_exempt, name='dispatch')
class ImportDataView(View):
    """GitHub Actions에서 JSON 데이터를 받아서 저장"""
    
    def post(self, request):
        try:
            # 간단한 토큰 확인
            auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'knu-crawl-2025')
            
            if auth_token != expected_token:
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # JSON 데이터 파싱
            data = json.loads(request.body)
            notices_data = data.get('notices', [])
            
            if not notices_data:
                return JsonResponse({'error': 'No notices data'}, status=400)
            
            # 기존 공지사항 삭제 후 새로 저장
            Notice.objects.all().delete()
            
            saved_count = 0
            for notice_data in notices_data:
                try:
                    # 게시판 찾기
                    board = NoticeBoard.objects.filter(name=notice_data['board_name']).first()
                    if not board:
                        continue
                    
                    # 공지사항 저장
                    Notice.objects.create(
                        board=board,
                        title=notice_data['title'],
                        url=notice_data['url'],
                        published_date=datetime.fromisoformat(notice_data['date']).date(),
                        display_order=notice_data.get('display_order', 0),
                        crawled_at=datetime.fromisoformat(notice_data['crawled_at'])
                    )
                    saved_count += 1
                except Exception:
                    continue
            
            return JsonResponse({
                'success': True,
                'saved_count': saved_count
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
            # 기존 데이터 삭제 (전체 갱신)
            Notice.objects.all().delete()
            
            created_count = 0
            
            for notice_data in notices_data:
                try:
                    # 카테고리 생성 또는 가져오기
                    category, _ = NoticeCategory.objects.get_or_create(
                        name=notice_data['category_name'],
                        defaults={'is_active': True}
                    )
                    
                    # 게시판 생성 또는 가져오기
                    board, _ = NoticeBoard.objects.get_or_create(
                        name=notice_data['board_name'],
                        defaults={
                            'category': category,
                            'url': f"https://www.kongju.ac.kr/board/{notice_data['board_name'].lower()}",
                            'is_active': True
                        }
                    )
                    
                    # 공지사항 생성
                    Notice.objects.create(
                        title=notice_data['title'],
                        url=notice_data['url'],
                        date=datetime.fromisoformat(notice_data['date']) if notice_data['date'] else None,
                        category=category,
                        board=board,
                        display_order=notice_data.get('display_order', 0)
                    )
                    created_count += 1
                        
                except Exception as e:
                    print(f"Error processing notice: {str(e)}")
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Data import completed: {created_count} notices imported',
                'imported': created_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
