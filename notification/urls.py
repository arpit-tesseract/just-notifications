from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
    path('', views.NotificationView.as_view(), name='api_list'),
    path('<int:pk>/', views.NotificationView.as_view(), name='api_detail'),
    path('mark-read/', views.MarkNotificationReadView.as_view(), name='mark_all_read'),
    path('mark-read/<int:pk>/', views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('archive/<int:pk>/', views.ArchiveNotificationView.as_view(), name='archive'),
]