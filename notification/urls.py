from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='api_list'),
    path('mark-read/<int:pk>/', views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
]