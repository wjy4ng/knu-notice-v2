from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from notices.tasks import setup_initial_data
import os


class ManualCrawlView(View):
    """수동 크롤링 실행 API"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """초기 데이터 설정 (크롤링은 GitHub Actions에서 담당)"""
        try:
            # 보안을 위한 간단한 토큰 확인
            auth_token = request.headers.get('Authorization')
            expected_token = os.getenv('CRAWL_AUTH_TOKEN', 'knu-crawl-2025')
            
            if auth_token != f'Bearer {expected_token}':
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # 초기 데이터 설정
            result = setup_initial_data()
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
