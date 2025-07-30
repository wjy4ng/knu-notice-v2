from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from notices.models import NoticeCategory, NoticeBoard, Notice
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ImportDataView(View):
    """GitHub Actions에서 JSON 데이터를 받아서 저장"""
    
    def post(self, request):
        """JSON 데이터를 받아서 데이터베이스에 저장"""
        try:
            # 보안을 위한 토큰 확인
            auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'default-token')
            
            if not auth_token or auth_token != expected_token:
                logger.warning(f"Unauthorized import attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # Content-Type 확인
            if request.content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)
            
            # 요청 크기 제한 (10MB)
            if len(request.body) > 10 * 1024 * 1024:
                return JsonResponse({'error': 'Request too large'}, status=413)
            
            # JSON 데이터 파싱
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            
            notices_data = data.get('notices', [])
            
            if not notices_data:
                return JsonResponse({'error': 'No notices data provided'}, status=400)
            
            if len(notices_data) > 1000:  # 최대 1000개 제한
                return JsonResponse({'error': 'Too many notices (max 1000)'}, status=400)
            
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
