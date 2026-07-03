from django.contrib import admin
from .models import (
    NotificationPriority,
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
    NotificationTemplate,
    Notification,
    NotificationAttachment,
    NotificationRecipient,
    NotificationPreference,
    NotificationQueue,
    NotificationLog
)

@admin.register(NotificationPriority)
class NotificationPriorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_default', 'is_active')
    search_fields = ('name', 'code')

@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_default', 'is_active')
    search_fields = ('name', 'code')

@admin.register(NotificationStatus)
class NotificationStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_final', 'is_default', 'is_active')
    search_fields = ('name', 'code')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'category', 'priority', 'is_active')
    list_filter = ('category', 'priority', 'is_active')
    search_fields = ('code', 'title', 'body')

class NotificationAttachmentInline(admin.TabularInline):
    model = NotificationAttachment
    extra = 0

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'priority', 'is_system_generated', 'created_at')
    list_filter = ('category', 'priority', 'is_system_generated', 'created_at')
    search_fields = ('id', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [NotificationAttachmentInline]

@admin.register(NotificationAttachment)
class NotificationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('notification', 'file', 'file_name', 'file_type', 'file_size')
    list_filter = ('file_type',)
    search_fields = ('notification__title', 'file_name')

class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0

@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'is_seen', 'seen_at', 'is_read', 'read_at', 'is_archived', 'archived_at')
    list_filter = ('is_seen', 'is_read', 'is_archived')
    search_fields = ('notification__title', 'user__username', 'user__email')

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'in_app', 'email')
    list_filter = ('in_app', 'email')
    search_fields = ('user__username', 'user__email')

@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ('notification', 'recipient', 'channel', 'status', 'scheduled_at', 'processed_at')
    list_filter = ('status', 'channel', 'scheduled_at', 'processed_at')
    search_fields = ('notification__title', 'recipient__username', 'recipient__email')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'recipient', 'channel', 'status', 'delivered_at')
    list_filter = ('channel', 'status', 'delivered_at')
    search_fields = ('notification__title', 'recipient__user__username', 'recipient__user__email', 'error_message')
