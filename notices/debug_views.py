from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt
def debug_env(request):
    """환경변수 디버깅용 (개발 전용)"""
    if not os.getenv('DEBUG', 'False').lower() == 'true':
        return JsonResponse({'error': 'Not available in production'}, status=403)
    
    return JsonResponse({
        'DATABASE_URL': os.getenv('DATABASE_URL', 'Not set')[:50] + '...' if os.getenv('DATABASE_URL') else 'Not set',
        'DJANGO_SECRET_KEY': 'Set' if os.getenv('DJANGO_SECRET_KEY') else 'Not set',
        'RENDER': os.getenv('RENDER', 'Not set'),
    })
