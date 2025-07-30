from django.urls import path
from . import views

app_name = "notices"

# http://localhost:8000/...
urlpatterns = [
    path('', views.index, name='index'),
    path('api/notice-counts/', views.get_notice_counts, name='notice_counts'),
    path('api/notice-preview/', views.get_notice_preview, name='notice_preview'),
    path('proxy/', views.proxy_view, name='proxy_view'),
]
