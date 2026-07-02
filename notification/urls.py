from django.urls import path

from .views import *

app_name = "notification"

urlpatterns = [
    # Master APIs
    path("categories/", NotificationCategoryListCreateAPIView.as_view(), name="notification-category-list"),
    path("categories/<int:pk>/", NotificationCategoryDetailAPIView.as_view(), name="notification-category-detail"),
    path("priorities/", NotificationPriorityListCreateAPIView.as_view(), name="notification-priority-list"),
    path("priorities/<int:pk>/", NotificationPriorityDetailAPIView.as_view(), name="notification-priority-detail"),
    path("channels/", NotificationChannelListCreateAPIView.as_view(), name="notification-channel-list"),
    path("channels/<int:pk>/", NotificationChannelDetailAPIView.as_view(), name="notification-channel-detail"),
    path("statuses/", NotificationStatusListCreateAPIView.as_view(), name="notification-status-list"),
    path("statuses/<int:pk>/", NotificationStatusDetailAPIView.as_view(), name="notification-status-detail"),
    path("templates/", NotificationTemplateListCreateAPIView.as_view(), name="notification-template-list"),
    path("templates/<int:pk>/", NotificationTemplateDetailAPIView.as_view(), name="notification-template-detail"),

    # Notification APIs
    path("", NotificationListCreateAPIView.as_view(), name="notification-list-create"),
    path("<int:pk>/", NotificationDetailAPIView.as_view(), name="notification-detail"),

    # User APIs
    path("my/", MyNotificationAPIView.as_view(), name="notification-my"),
    path("unread/", MyNotificationAPIView.as_view(), name="notification-unread"),
    path("archived/", MyNotificationAPIView.as_view(), name="notification-archived"),
    path("history/", MyNotificationAPIView.as_view(), name="notification-history"),

    # Action APIs
    path("<int:pk>/mark-read/", MarkNotificationReadAPIView.as_view(), name="notification-mark-read"),
    path("<int:pk>/mark-seen/", MarkNotificationSeenAPIView.as_view(), name="notification-mark-seen"),
    path("<int:pk>/archive/", ArchiveNotificationAPIView.as_view(), name="notification-archive"),
    path("<int:pk>/restore/", ArchiveNotificationAPIView.as_view(), name="notification-restore"),
    path("mark-all-read/", MarkNotificationReadAPIView.as_view(), name="notification-mark-all-read"),
    path("mark-all-seen/", MarkNotificationSeenAPIView.as_view(), name="notification-mark-all-seen"),
    path("archive-all/", ArchiveNotificationAPIView.as_view(), name="notification-archive-all"),

    # Attachments
    path("attachments/", NotificationAttachmentAPIView.as_view(), name="notification-attachment-list"),
    path("attachments/<int:pk>/", NotificationAttachmentAPIView.as_view(), name="notification-attachment-detail"),

    # Preferences
    path("preferences/", NotificationPreferenceAPIView.as_view(), name="notification-preference"),

    # Queue APIs
    path("queue/", NotificationQueueAPIView.as_view(), name="notification-queue-list"),
    path("queue/<int:pk>/", NotificationQueueAPIView.as_view(), name="notification-queue-detail"),

    # Log APIs
    path("logs/", NotificationLogAPIView.as_view(), name="notification-log-list"),
    path("logs/<int:pk>/", NotificationLogAPIView.as_view(), name="notification-log-detail"),

    # Dashboard APIs
    path("dashboard/", MyNotificationAPIView.as_view(), name="notification-dashboard"),
    path("dashboard/unread-count/", MyNotificationAPIView.as_view(), name="notification-dashboard-unread-count"),
    path("dashboard/statistics/", MyNotificationAPIView.as_view(), name="notification-dashboard-statistics"),
    path("dashboard/recent/", MyNotificationAPIView.as_view(), name="notification-dashboard-recent"),

    # Bulk APIs
    path("bulk-send/", NotificationListCreateAPIView.as_view(), name="notification-bulk-send"),
    path("broadcast/", NotificationListCreateAPIView.as_view(), name="notification-broadcast"),
    path("schedule/", NotificationListCreateAPIView.as_view(), name="notification-schedule"),

    # Search APIs
    path("search/", NotificationListCreateAPIView.as_view(), name="notification-search"),
    path("search/templates/", NotificationTemplateListCreateAPIView.as_view(), name="notification-search-templates"),
    path("search/logs/", NotificationLogAPIView.as_view(), name="notification-search-logs"),
]
