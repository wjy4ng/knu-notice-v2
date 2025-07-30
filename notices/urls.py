from django.urls import path
from . import views
from .manual_crawl import ManualCrawlView
from .import_views import ImportDataView

app_name = "notices"

# http://localhost:8000/...
urlpatterns = [
    path('', views.index, name='index'),
    path('api/notice-counts/', views.get_notice_counts, name='notice_counts'),
    path('api/notice-preview/', views.get_notice_preview, name='notice_preview'),
    path('api/manual-crawl/', ManualCrawlView.as_view(), name='manual_crawl'),
    path('api/import-data/', ImportDataView.as_view(), name='import_data'),
]
