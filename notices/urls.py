from django.urls import path
from . import views

app_name = "notices"

# http://localhost:8000/...
urlpatterns = [
    path('', views.index, name='index'),
    path('proxy/', views.proxy_view, name='proxy_view'),
    path('api/get-notice-count/', views.get_notice_count, name='get_notice_count'),
]
