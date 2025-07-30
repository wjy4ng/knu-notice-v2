from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os

@csrf_exempt
def debug_env(request):
    """환경변수 디버깅용 (개발 전용)"""
    # 프로덕션 환경에서는 접근 차단
    if not settings.DEBUG:
        return JsonResponse({'error': 'Debug views not available in production'}, status=403)
    
    # 로컬 개발 환경에서만 허용
    if not request.META.get('HTTP_HOST', '').startswith('localhost') and not request.META.get('HTTP_HOST', '').startswith('127.0.0.1'):
        return JsonResponse({'error': 'Debug views only available on localhost'}, status=403)
    
    return JsonResponse({
        'DATABASE_URL': 'Set' if os.getenv('DATABASE_URL') else 'Not set',
        'DJANGO_SECRET_KEY': 'Set' if os.getenv('DJANGO_SECRET_KEY') else 'Not set',
        'RENDER': os.getenv('RENDER', 'Not set'),
        'DEBUG': str(settings.DEBUG),
        'GITHUB_ACTIONS': os.getenv('GITHUB_ACTIONS', 'Not set'),
    })
