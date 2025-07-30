from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from notices.tasks import crawl_all_notices
import json
import os


class ManualCrawlView(View):
    """수동 크롤링 실행 API (무료 버전용)"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """크롤링을 수동으로 실행"""
        try:
            # Render.com 환경에서는 크롤링 비활성화
            if os.getenv('RENDER'):
                return JsonResponse({
                    'success': False,
                    'error': 'Crawling is disabled on Render.com. Use GitHub Actions for automated crawling.',
                    'message': 'GitHub Actions를 사용하여 크롤링하세요.'
                }, status=400)
            
            # 보안을 위한 간단한 토큰 확인
            auth_token = request.headers.get('Authorization')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'knu-crawl-2025')
            
            if auth_token != f'Bearer {expected_token}':
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # 크롤링 실행
            result = crawl_all_notices()
            
            return JsonResponse({
                'success': True,
                'message': 'Crawling completed successfully',
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
            'message': 'Use POST request to trigger crawling'
        })
