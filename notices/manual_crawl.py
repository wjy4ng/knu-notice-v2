from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from notices.tasks import setup_initial_data
import os
import logging

logger = logging.getLogger(__name__)

class ManualCrawlView(View):
    """수동 크롤링 실행 API"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """초기 데이터 설정 (크롤링은 GitHub Actions에서 담당)"""
        try:
            # 보안을 위한 간단한 토큰 확인
            auth_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'default-token')
            
            if not auth_token or auth_token != expected_token:
                logger.warning(f"Unauthorized manual crawl attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # Rate limiting - 프로덕션에서는 더 엄격하게
            if not settings.DEBUG:
                # 실제 프로덕션에서는 Redis 등을 사용한 rate limiting 권장
                pass
            
            # 초기 데이터 설정
            result = setup_initial_data()
            logger.info(f"Manual crawl setup completed from {request.META.get('REMOTE_ADDR', 'unknown')}")
            
            return JsonResponse({
                'success': True,
                'message': 'Initial data setup completed. Crawling is handled by GitHub Actions.',
                'result': str(result)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """크롤링 상태 확인"""
        return JsonResponse({
            'service': 'KNU Notice Crawler',
            'status': 'ready',
            'message': 'Crawling is handled by GitHub Actions every hour'
        })
