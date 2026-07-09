from django.contrib import admin

from .models import (
    Notification,
    NotificationCategory,
    NotificationRecipient,
    NotificationStatusLog,
    NotificationTemplate,
)


@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "display_name")

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "category", "templatefile", "is_active", "created_at")
    
    list_filter = ("is_active", "category")
    
    search_fields = ("name", "title", "content", "category__name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "template", "is_active", "created_at")
    list_filter = ("status", "is_active", "created_at")
    search_fields = ("title", "content", "template__title")


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ("user", "notification", "channel", "status", "delivery_status", "read_at")
    list_filter = ("channel", "status", "delivery_status")
    search_fields = ("user__email", "user__username", "notification__title")


@admin.register(NotificationStatusLog)
class NotificationStatusLogAdmin(admin.ModelAdmin):
    list_display = ("notification", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("notification__title", "summary")


