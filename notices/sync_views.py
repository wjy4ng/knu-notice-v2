from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from notices.models import NoticeCategory, NoticeBoard, Notice
from datetime import datetime
import json
import os

@method_decorator(csrf_exempt, name='dispatch')
class SyncDataView(View):
    """GitHub Actions에서 크롤링한 데이터를 받아서 Render.com DB에 저장"""
    
    def post(self, request):
        """크롤링된 데이터를 받아서 저장"""
        try:
            # 보안을 위한 토큰 확인
            auth_token = request.headers.get('Authorization')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'knu-crawl-2025')
            
            if auth_token != f'Bearer {expected_token}':
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # JSON 데이터 파싱
            data = json.loads(request.body)
            notices_data = data.get('notices', [])
            
            if not notices_data:
                return JsonResponse({'error': 'No notices data provided'}, status=400)
            
            # 데이터 저장
            created_count = 0
            updated_count = 0
            
            for notice_data in notices_data:
                try:
                    # 카테고리 생성 또는 가져오기
                    category, _ = NoticeCategory.objects.get_or_create(
                        name=notice_data['category'],
                        defaults={'is_active': True}
                    )
                    
                    # 게시판 생성 또는 가져오기
                    board, _ = NoticeBoard.objects.get_or_create(
                        name=notice_data['board'],
                        defaults={
                            'category': category,
                            'url': f"https://www.kongju.ac.kr/board/{notice_data['board'].lower()}",
                            'is_active': True
                        }
                    )
                    
                    # 공지사항 생성 또는 업데이트
                    notice, created = Notice.objects.get_or_create(
                        url=notice_data['url'],
                        defaults={
                            'title': notice_data['title'],
                            'date': datetime.fromisoformat(notice_data['date']) if notice_data['date'] else None,
                            'category': category,
                            'board': board,
                            'display_order': notice_data.get('display_order', 0)
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        # 기존 데이터 업데이트
                        notice.title = notice_data['title']
                        notice.display_order = notice_data.get('display_order', 0)
                        notice.save()
                        updated_count += 1
                        
                except Exception as e:
                    print(f"Error processing notice: {str(e)}")
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Data sync completed: {created_count} created, {updated_count} updated',
                'created': created_count,
                'updated': updated_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
