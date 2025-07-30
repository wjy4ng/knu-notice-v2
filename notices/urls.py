from django.urls import path, include
from . import views
from .import_views import ImportDataView

app_name = "notices"

# API v1 패턴들
api_v1_patterns = [
    path('notice-counts/', views.get_notice_counts, name='notice_counts'),
    path('notice-preview/', views.get_notice_preview, name='notice_preview'),
    path('import-data/', ImportDataView.as_view(), name='import_data'),
]

# 메인 URL 패턴들
urlpatterns = [
    path('', views.index, name='index'),
    path('api/v1/', include(api_v1_patterns)),
]
