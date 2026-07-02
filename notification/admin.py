from django.contrib import admin

from .models import (
    Notification,
    NotificationAttachment,
    NotificationCategory,
    NotificationChannel,
    NotificationLog,
    NotificationPreference,
    NotificationPriority,
    NotificationQueue,
    NotificationRecipient,
    NotificationStatus,
    NotificationTemplate,
)


class SoftDeleteAdminMixin:
    """Provide soft-delete actions and readonly fields for admin models."""

    actions = ["soft_delete_selected", "restore_selected"]

    def get_queryset(self, request):
        return self.model.all_objects.all()

    def delete_model(self, request, obj):
        obj.soft_delete(user=request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if not obj.is_deleted:
                obj.soft_delete(user=request.user)

    def soft_delete_selected(self, request, queryset):
        count = 0
        for obj in queryset:
            if not obj.is_deleted:
                obj.soft_delete(user=request.user)
                count += 1
        self.message_user(request, f"Successfully soft-deleted {count} records.")

    soft_delete_selected.short_description = "Soft-delete selected records"

    def restore_selected(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f"Successfully restored {count} records.")

    restore_selected.short_description = "Restore selected records"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = {"created_at", "updated_at", "is_deleted", "deleted_at", "deleted_by"}
        declared = set(getattr(self, "readonly_fields", ()))
        return tuple(readonly_fields | declared)


class AuditAdminMixin:
    """Expose audit timestamps as readonly fields in the admin UI."""

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = {"created_at", "updated_at"}
        declared = set(getattr(self, "readonly_fields", ()))
        return tuple(readonly_fields | declared)


@admin.register(NotificationPriority)
class NotificationPriorityAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "display_order", "is_default", "is_active", "is_deleted")
    search_fields = ("name", "code")
    list_filter = ("is_default", "is_active", "is_deleted")
    ordering = ("display_order",)
    fieldsets = (
        ("Primary Information", {"fields": ("name", "code", "display_order")}),
        ("Visual Configuration", {"fields": ("color", "icon")}),
        ("Status & Settings", {"fields": ("is_default", "is_active")}),
        ("Description", {"fields": ("description",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )


@admin.register(NotificationCategory)
class NotificationCategoryAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "is_deleted")
    search_fields = ("name", "code")
    list_filter = ("is_active", "is_deleted")
    ordering = ("name",)
    fieldsets = (
        ("Primary Information", {"fields": ("name", "code")}),
        ("Visual Configuration", {"fields": ("color", "icon")}),
        ("Status & Settings", {"fields": ("is_active",)}),
        ("Description", {"fields": ("description",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("code", "title", "category", "priority", "is_active", "created_at")
    search_fields = ("code", "title", "body")
    list_filter = ("is_active", "category", "priority")
    autocomplete_fields = ("category", "priority")
    ordering = ("-created_at",)
    fieldsets = (
        ("Template Setup", {"fields": ("code", "category", "priority", "is_active")}),
        ("Template Content", {"fields": ("title", "body")}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "priority")


@admin.register(Notification)
class NotificationAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("title", "category", "priority", "is_system_generated", "is_deleted", "created_at")
    search_fields = ("title", "message")
    list_filter = ("is_system_generated", "is_deleted", "category", "priority")
    autocomplete_fields = ("category", "priority", "template")
    ordering = ("-created_at",)
    fieldsets = (
        ("Notification Details", {"fields": ("title", "category", "priority", "template", "is_system_generated")}),
        ("Content", {"fields": ("message", "action_url", "icon")}),
        ("Extra Data", {"fields": ("metadata",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "template", "priority")


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("user", "notification", "is_seen", "seen_at", "is_read", "read_at", "is_archived", "is_deleted")
    search_fields = ("user__full_name", "user__contact_no", "notification__title")
    list_filter = ("is_seen", "is_read", "is_archived", "is_deleted", "created_at")
    autocomplete_fields = ("user", "notification")
    ordering = ("-created_at",)
    fieldsets = (
        ("Associations", {"fields": ("notification", "user")}),
        ("Seen Information", {"fields": ("is_seen", "seen_at")}),
        ("Read Information", {"fields": ("is_read", "read_at")}),
        ("Archive Information", {"fields": ("is_archived", "archived_at")}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("notification", "user")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("user", "in_app", "email", "created_at")
    search_fields = ("user__full_name", "user__contact_no")
    list_filter = ("in_app", "email")
    autocomplete_fields = ("user",)
    filter_horizontal = ("enabled_categories",)
    ordering = ("user",)
    fieldsets = (
        ("User Profile", {"fields": ("user",)}),
        ("Delivery Preferences", {"fields": ("in_app", "email")}),
        ("Subscribed Categories", {"fields": ("enabled_categories",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").prefetch_related("enabled_categories")


@admin.register(NotificationAttachment)
class NotificationAttachmentAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("file_name", "file_type", "file_size", "notification", "is_deleted")
    search_fields = ("file_name", "file_type")
    list_filter = ("file_type", "is_deleted")
    autocomplete_fields = ("notification",)
    ordering = ("-created_at",)
    fieldsets = (
        ("Notification Link", {"fields": ("notification",)}),
        ("File Metadata", {"fields": ("file", "file_name", "file_type", "file_size")}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("notification")


@admin.register(NotificationChannel)
class NotificationChannelAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "display_order", "is_default", "is_active", "is_deleted")
    search_fields = ("name", "code")
    list_filter = ("is_default", "is_active", "is_deleted")
    ordering = ("display_order", "name")
    fieldsets = (
        ("Primary Information", {"fields": ("name", "code", "display_order")}),
        ("Visual Configuration", {"fields": ("color", "icon")}),
        ("Status & Settings", {"fields": ("is_default", "is_active")}),
        ("Description", {"fields": ("description",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )


@admin.register(NotificationStatus)
class NotificationStatusAdmin(SoftDeleteAdminMixin, AuditAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "is_final", "is_default", "is_active", "is_deleted")
    search_fields = ("name", "code")
    list_filter = ("is_final", "is_default", "is_active", "is_deleted")
    ordering = ("display_order", "name")
    fieldsets = (
        ("Primary Information", {"fields": ("name", "code", "display_order")}),
        ("Configuration", {"fields": ("is_final", "is_default", "is_active")}),
        ("Visual Configuration", {"fields": ("color", "icon")}),
        ("Description", {"fields": ("description",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
        ("Soft Delete Info", {"fields": ("is_deleted", "deleted_at", "deleted_by"), "classes": ("collapse",)}),
    )


@admin.register(NotificationQueue)
class NotificationQueueAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("notification", "recipient", "channel", "status", "scheduled_at", "processed_at", "retry_count", "priority")
    search_fields = ("recipient__full_name", "recipient__contact_no", "notification__title", "celery_task_id", "error_message")
    list_filter = ("status", "channel", "priority", "scheduled_at")
    autocomplete_fields = ("notification", "recipient", "channel", "status")
    ordering = ("priority", "scheduled_at", "created_at")
    fieldsets = (
        ("Task Settings", {"fields": ("notification", "recipient", "channel", "status", "priority")}),
        ("Timing Detail", {"fields": ("scheduled_at", "processed_at", "next_retry_at")}),
        ("Job Details", {"fields": ("retry_count", "max_retry", "celery_task_id", "error_message")}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("notification", "recipient", "channel", "status")


@admin.register(NotificationLog)
class NotificationLogAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("notification", "recipient", "channel", "status", "retry_count", "delivered_at")
    search_fields = ("recipient__user__full_name", "recipient__user__contact_no", "notification__title", "error_message")
    list_filter = ("status", "channel", "created_at")
    autocomplete_fields = ("notification", "recipient", "channel", "status")
    ordering = ("-created_at",)
    fieldsets = (
        ("Log Information", {"fields": ("notification", "recipient", "channel", "status")}),
        ("Processing Statistics", {"fields": ("retry_count", "delivered_at", "error_message")}),
        ("Payload Response", {"fields": ("response",)}),
        ("Audit Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("notification", "recipient", "recipient__user", "channel", "status")
