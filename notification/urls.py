from django.urls import path
from .views import (
    NotificationPriorityAPIView,
    NotificationCategoryAPIView,
    NotificationChannelAPIView,
    NotificationStatusAPIView,
    NotificationTemplateAPIView,
    NotificationAPIView,
    SystemNotificationAPIView,
    NotificationAttachmentAPIView,
    MyNotificationAPIView,
    NotificationPreferenceAPIView,
    NotificationQueueAPIView,
    NotificationLogAPIView
)

urlpatterns = [
    # Master Data APIs (Admin)
    path('priorities/', NotificationPriorityAPIView.as_view(), name='priority-list'),
    path('priorities/<int:pk>/', NotificationPriorityAPIView.as_view(), name='priority-detail'),
    
    path('categories/', NotificationCategoryAPIView.as_view(), name='category-list'),
    path('categories/<int:pk>/', NotificationCategoryAPIView.as_view(), name='category-detail'),
    
    path('channels/', NotificationChannelAPIView.as_view(), name='channel-list'),
    path('channels/<int:pk>/', NotificationChannelAPIView.as_view(), name='channel-detail'),
    
    path('statuses/', NotificationStatusAPIView.as_view(), name='status-list'),
    path('statuses/<int:pk>/', NotificationStatusAPIView.as_view(), name='status-detail'),
    
    path('templates/', NotificationTemplateAPIView.as_view(), name='template-list'),
    path('templates/<int:pk>/', NotificationTemplateAPIView.as_view(), name='template-detail'),
    
    # Notification & Attachment Management (Admin)
    path('notifications/', NotificationAPIView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', NotificationAPIView.as_view(), name='notification-detail'),
    path('notifications/system/', SystemNotificationAPIView.as_view(), name='system-notification-create'),
    
    path('attachments/', NotificationAttachmentAPIView.as_view(), name='attachment-list'),
    path('attachments/<int:pk>/', NotificationAttachmentAPIView.as_view(), name='attachment-detail'),
    
    # User Inbox & Preference APIs (Authenticated User)
    path('my-notifications/', MyNotificationAPIView.as_view(), name='my-notification-list'),
    path('my-notifications/<int:pk>/', MyNotificationAPIView.as_view(), name='my-notification-detail'),
    path('preferences/', NotificationPreferenceAPIView.as_view(), name='preference'),
    
    # Queue & Delivery Log APIs (Admin)
    path('queue/', NotificationQueueAPIView.as_view(), name='queue-list'),
    path('queue/<int:pk>/', NotificationQueueAPIView.as_view(), name='queue-detail'),
    
    path('logs/', NotificationLogAPIView.as_view(), name='log-list'),
    path('logs/<int:pk>/', NotificationLogAPIView.as_view(), name='log-detail'),
]