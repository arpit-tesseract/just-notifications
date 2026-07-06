from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('api/', views.notification_api_view, name='api_list'),
    path('mark-read/<int:pk>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
