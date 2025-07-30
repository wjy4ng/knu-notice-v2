from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
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
        try:
            # 간단한 토큰 확인
            auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN')
            
            if not expected_token:
                logger.error("CRAWL_AUTH_TOKEN 환경 변수가 설정되지 않았습니다.")
                return JsonResponse({'error': 'Internal Server Error'}, status=500)
            
            if auth_token != expected_token:
                logger.warning("인증 실패: 잘못된 토큰")
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # JSON 데이터 파싱
            try:
                data = json.loads(request.body)
                notices_data = data.get('notices', [])
            except json.JSONDecodeError as e:
                logger.error(f"JSON 디코딩 오류: {str(e)}")
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            
            if not notices_data:
                logger.warning("공지사항 데이터가 없습니다.")
                return JsonResponse({'error': 'No notices data'}, status=400)
            
            saved_count = 0
            for notice_data in notices_data:
                try:
                    # 데이터 유효성 검사
                    if not all(key in notice_data for key in ('title', 'url', 'date', 'board_name', 'crawled_at')):
                        logger.warning(f"필수 필드 누락: {notice_data}")
                        continue

                    # 게시판 찾기
                    board = NoticeBoard.objects.filter(name=notice_data['board_name']).first()
                    if not board:
                        logger.warning(f"게시판을 찾을 수 없음: {notice_data['board_name']}")
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
                    logger.error(f"공지사항 처리 중 오류: {str(e)}, 데이터: {notice_data}")
                    continue
            
            return JsonResponse({
                'success': True,
                'saved_count': saved_count
            })
            
        except Exception as e:
            logger.exception("예상치 못한 오류 발생")
            return JsonResponse({'error': str(e)}, status=500)