from django.urls import path, include
from . import views
from .manual_crawl import ManualCrawlView
from .import_views import ImportDataView
from .debug_views import debug_env

app_name = "notices"

# API v1 패턴들
api_v1_patterns = [
    path('notice-counts/', views.get_notice_counts, name='notice_counts'),
    path('notice-preview/', views.get_notice_preview, name='notice_preview'),
    path('manual-crawl/', ManualCrawlView.as_view(), name='manual_crawl'),
    path('import-data/', ImportDataView.as_view(), name='import_data'),
]

# 디버그 패턴들 (개발 전용)
debug_patterns = [
    path('env/', debug_env, name='debug_env'),
]

# 메인 URL 패턴들
urlpatterns = [
    path('', views.index, name='index'),
    path('api/v1/', include(api_v1_patterns)),
    path('debug/', include(debug_patterns)),
]
