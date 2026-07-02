from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.db import models

from user.models import User
from user.serializers import UserBasicDetailsOutputSerializer
from .models import (
    NotificationPriority,
    NotificationCategory,
    NotificationTemplate,
    Notification,
    NotificationRecipient,
    NotificationPreference,
    NotificationAttachment,
    NotificationChannel,
    NotificationStatus,
    NotificationQueue,
    NotificationLog,
)


# ==========================================
# 1. NotificationPriority Serializers
# ==========================================

class NotificationPriorityInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPriority
        fields = (
            'name',
            'code',
            'description',
            'color',
            'icon',
            'display_order',
            'is_default',
            'is_active',
        )

    def validate_display_order(self, value):
        if value < 0:
            raise ValidationError("Display order must be a non-negative integer.")
        return value

    def validate_name(self, value):
        # Case-insensitive uniqueness check
        qs = NotificationPriority.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A priority with this name already exists.")
        return value

    def validate_code(self, value):
        # Case-insensitive uniqueness check
        qs = NotificationPriority.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A priority with this code already exists.")
        return value


class NotificationPriorityOutputSerializer(serializers.ModelSerializer):
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationPriority
        fields = '__all__'


class NotificationPriorityDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPriority
        fields = ('id', 'name', 'code', 'color', 'icon')


class NotificationPriorityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPriority
        fields = (
            'id',
            'name',
            'code',
            'display_order',
            'is_default',
            'is_active',
            'is_deleted',
        )


# ==========================================
# 2. NotificationCategory Serializers
# ==========================================

class NotificationCategoryInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        fields = (
            'name',
            'code',
            'description',
            'icon',
            'color',
            'is_active',
        )

    def validate_name(self, value):
        qs = NotificationCategory.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A category with this name already exists.")
        return value

    def validate_code(self, value):
        qs = NotificationCategory.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A category with this code already exists.")
        return value


class NotificationCategoryOutputSerializer(serializers.ModelSerializer):
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationCategory
        fields = '__all__'


class NotificationCategoryDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        fields = ('id', 'name', 'code', 'color', 'icon')


class NotificationCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        fields = (
            'id',
            'name',
            'code',
            'is_active',
            'is_deleted',
        )


# ==========================================
# 3. NotificationTemplate Serializers
# ==========================================

class NotificationTemplateInputSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=NotificationCategory.objects.filter(is_deleted=False)
    )
    priority = serializers.PrimaryKeyRelatedField(
        queryset=NotificationPriority.objects.filter(is_deleted=False)
    )

    class Meta:
        model = NotificationTemplate
        fields = (
            'category',
            'code',
            'title',
            'body',
            'priority',
            'is_active',
        )

    def validate_code(self, value):
        qs = NotificationTemplate.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A template with this code already exists.")
        return value


class NotificationTemplateOutputSerializer(serializers.ModelSerializer):
    category = NotificationCategoryDropdownSerializer(read_only=True)
    priority = NotificationPriorityDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = (
            'id',
            'category',
            'code',
            'title',
            'body',
            'priority',
            'is_active',
            'created_at',
            'updated_at',
        )


class NotificationTemplateDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ('id', 'code', 'title')


class NotificationTemplateListSerializer(serializers.ModelSerializer):
    category = NotificationCategoryDropdownSerializer(read_only=True)
    priority = NotificationPriorityDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = (
            'id',
            'category',
            'code',
            'title',
            'priority',
            'is_active',
            'created_at',
        )


# ==========================================
# 4. Notification Serializers
# ==========================================

class NotificationInputSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=NotificationCategory.objects.filter(is_deleted=False)
    )
    template = serializers.PrimaryKeyRelatedField(
        queryset=NotificationTemplate.objects.all(),
        required=False,
        allow_null=True
    )
    priority = serializers.PrimaryKeyRelatedField(
        queryset=NotificationPriority.objects.filter(is_deleted=False)
    )

    class Meta:
        model = Notification
        fields = (
            'category',
            'template',
            'title',
            'message',
            'priority',
            'action_url',
            'icon',
            'metadata',
            'is_system_generated',
        )

    def validate(self, attrs):
        category = attrs.get('category')
        template = attrs.get('template')

        # If a template is provided, validate that the category matches the template's category
        if template and template.category != category:
            raise ValidationError({
                "template": f"The selected template belongs to the category '{template.category.name}', which does not match the provided category '{category.name}'."
            })
        return attrs


class NotificationOutputSerializer(serializers.ModelSerializer):
    category = NotificationCategoryDropdownSerializer(read_only=True)
    template = NotificationTemplateDropdownSerializer(read_only=True)
    priority = NotificationPriorityDropdownSerializer(read_only=True)
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class NotificationDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title')


class NotificationListSerializer(serializers.ModelSerializer):
    category = NotificationCategoryDropdownSerializer(read_only=True)
    priority = NotificationPriorityDropdownSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'title',
            'category',
            'priority',
            'is_system_generated',
            'is_deleted',
            'created_at',
        )


# ==========================================
# 5. NotificationRecipient Serializers
# ==========================================

class NotificationRecipientInputSerializer(serializers.ModelSerializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.filter(is_deleted=False)
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_deleted=False)
    )

    class Meta:
        model = NotificationRecipient
        fields = (
            'notification',
            'user',
            'is_seen',
            'seen_at',
            'is_read',
            'read_at',
            'is_archived',
            'archived_at',
        )

    def validate(self, attrs):
        notification = attrs.get('notification')
        user = attrs.get('user')

        # Check unique_together constraint manually for inputs
        qs = NotificationRecipient.objects.filter(notification=notification, user=user)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This user is already a recipient of this notification.")

        # Auto-manage status timestamps
        # 1. Seen
        is_seen = attrs.get('is_seen', False)
        if is_seen:
            if not attrs.get('seen_at'):
                attrs['seen_at'] = timezone.now()
        else:
            attrs['seen_at'] = None

        # 2. Read
        is_read = attrs.get('is_read', False)
        if is_read:
            if not attrs.get('read_at'):
                attrs['read_at'] = timezone.now()
        else:
            attrs['read_at'] = None

        # 3. Archived
        is_archived = attrs.get('is_archived', False)
        if is_archived:
            if not attrs.get('archived_at'):
                attrs['archived_at'] = timezone.now()
        else:
            attrs['archived_at'] = None

        return attrs


class NotificationRecipientOutputSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    user = UserBasicDetailsOutputSerializer(read_only=True)
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = '__all__'


class NotificationRecipientDropdownSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    notification_title = serializers.CharField(source='notification.title', read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = ('id', 'user_name', 'notification_title')


class NotificationRecipientListSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    user = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = (
            'id',
            'notification',
            'user',
            'is_seen',
            'is_read',
            'is_archived',
            'created_at',
        )


# ==========================================
# 6. NotificationPreference Serializers
# ==========================================

class NotificationPreferenceInputSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_deleted=False)
    )
    enabled_categories = serializers.PrimaryKeyRelatedField(
        queryset=NotificationCategory.objects.filter(is_deleted=False, is_active=True),
        many=True,
        required=False
    )

    class Meta:
        model = NotificationPreference
        fields = (
            'user',
            'in_app',
            'email',
            'enabled_categories',
        )

    def validate_user(self, value):
        # Validate OneToOne mapping manually
        qs = NotificationPreference.objects.filter(user=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Notification preferences already exist for this user.")
        return value


class NotificationPreferenceOutputSerializer(serializers.ModelSerializer):
    user = UserBasicDetailsOutputSerializer(read_only=True)
    enabled_categories = NotificationCategoryDropdownSerializer(many=True, read_only=True)

    class Meta:
        model = NotificationPreference
        fields = (
            'id',
            'user',
            'in_app',
            'email',
            'enabled_categories',
            'created_at',
            'updated_at',
        )


class NotificationPreferenceDropdownSerializer(serializers.ModelSerializer):
    user_contact = serializers.CharField(source='user.contact_no', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ('id', 'user_contact')


class NotificationPreferenceListSerializer(serializers.ModelSerializer):
    user = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationPreference
        fields = (
            'id',
            'user',
            'in_app',
            'email',
        )


# ==========================================
# 7. NotificationAttachment Serializers
# ==========================================

class NotificationAttachmentInputSerializer(serializers.ModelSerializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.filter(is_deleted=False)
    )
    file_name = serializers.CharField(required=False)
    file_type = serializers.CharField(required=False)
    file_size = serializers.IntegerField(required=False)

    class Meta:
        model = NotificationAttachment
        fields = (
            'notification',
            'file',
            'file_name',
            'file_type',
            'file_size',
        )

    def validate(self, attrs):
        file_obj = attrs.get('file')
        if file_obj:
            # Auto-extract parameters from uploaded file if not explicitly supplied
            if not attrs.get('file_name'):
                attrs['file_name'] = file_obj.name
            if not attrs.get('file_type'):
                attrs['file_type'] = getattr(file_obj, 'content_type', 'application/octet-stream')
            if not attrs.get('file_size'):
                attrs['file_size'] = file_obj.size
        else:
            if not attrs.get('file_name') or not attrs.get('file_size'):
                raise ValidationError("File, file_name, and file_size are required fields.")

        return attrs


class NotificationAttachmentOutputSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationAttachment
        fields = '__all__'


class NotificationAttachmentDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationAttachment
        fields = ('id', 'file_name')


class NotificationAttachmentListSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationAttachment
        fields = (
            'id',
            'file_name',
            'file_type',
            'file_size',
            'notification',
        )


# ==========================================
# 8. NotificationChannel Serializers
# ==========================================

class NotificationChannelInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = (
            'name',
            'code',
            'description',
            'icon',
            'color',
            'display_order',
            'is_default',
            'is_active',
        )

    def validate_display_order(self, value):
        if value < 0:
            raise ValidationError("Display order must be a non-negative integer.")
        return value

    def validate_name(self, value):
        qs = NotificationChannel.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A channel with this name already exists.")
        return value

    def validate_code(self, value):
        qs = NotificationChannel.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A channel with this code already exists.")
        return value


class NotificationChannelOutputSerializer(serializers.ModelSerializer):
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationChannel
        fields = '__all__'


class NotificationChannelDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = ('id', 'name', 'code', 'color', 'icon')


class NotificationChannelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = (
            'id',
            'name',
            'code',
            'display_order',
            'is_default',
            'is_active',
            'is_deleted',
        )


# ==========================================
# 9. NotificationStatus Serializers
# ==========================================

class NotificationStatusInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatus
        fields = (
            'name',
            'code',
            'description',
            'color',
            'icon',
            'display_order',
            'is_final',
            'is_default',
            'is_active',
        )

    def validate_display_order(self, value):
        if value < 0:
            raise ValidationError("Display order must be a non-negative integer.")
        return value

    def validate_name(self, value):
        qs = NotificationStatus.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A status with this name already exists.")
        return value

    def validate_code(self, value):
        qs = NotificationStatus.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A status with this code already exists.")
        return value


class NotificationStatusOutputSerializer(serializers.ModelSerializer):
    deleted_by = UserBasicDetailsOutputSerializer(read_only=True)

    class Meta:
        model = NotificationStatus
        fields = '__all__'


class NotificationStatusDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatus
        fields = ('id', 'name', 'code', 'color', 'icon')


class NotificationStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatus
        fields = (
            'id',
            'name',
            'code',
            'display_order',
            'is_final',
            'is_default',
            'is_active',
            'is_deleted',
        )


# ==========================================
# 10. NotificationQueue Serializers
# ==========================================

class NotificationQueueInputSerializer(serializers.ModelSerializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.filter(is_deleted=False)
    )
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_deleted=False)
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=NotificationChannel.objects.filter(is_deleted=False, is_active=True)
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=NotificationStatus.objects.filter(is_deleted=False, is_active=True)
    )

    class Meta:
        model = NotificationQueue
        fields = (
            'notification',
            'recipient',
            'channel',
            'status',
            'scheduled_at',
            'processed_at',
            'retry_count',
            'max_retry',
            'next_retry_at',
            'celery_task_id',
            'error_message',
            'priority',
        )


class NotificationQueueOutputSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    recipient = UserBasicDetailsOutputSerializer(read_only=True)
    channel = NotificationChannelDropdownSerializer(read_only=True)
    status = NotificationStatusDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationQueue
        fields = (
            'id',
            'notification',
            'recipient',
            'channel',
            'status',
            'scheduled_at',
            'processed_at',
            'retry_count',
            'max_retry',
            'next_retry_at',
            'celery_task_id',
            'error_message',
            'priority',
            'created_at',
            'updated_at',
        )


class NotificationQueueDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationQueue
        fields = ('id', 'celery_task_id')


class NotificationQueueListSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    recipient = UserBasicDetailsOutputSerializer(read_only=True)
    channel = NotificationChannelDropdownSerializer(read_only=True)
    status = NotificationStatusDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationQueue
        fields = (
            'id',
            'notification',
            'recipient',
            'channel',
            'status',
            'scheduled_at',
            'processed_at',
            'priority',
        )


# ==========================================
# 11. NotificationLog Serializers
# ==========================================

class NotificationLogInputSerializer(serializers.ModelSerializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.filter(is_deleted=False)
    )
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=NotificationRecipient.objects.filter(is_deleted=False)
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=NotificationChannel.objects.filter(is_deleted=False, is_active=True)
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=NotificationStatus.objects.filter(is_deleted=False, is_active=True)
    )

    class Meta:
        model = NotificationLog
        fields = (
            'notification',
            'recipient',
            'channel',
            'status',
            'retry_count',
            'response',
            'error_message',
            'delivered_at',
        )


class NotificationLogOutputSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    recipient = NotificationRecipientDropdownSerializer(read_only=True)
    channel = NotificationChannelDropdownSerializer(read_only=True)
    status = NotificationStatusDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationLog
        fields = (
            'id',
            'notification',
            'recipient',
            'channel',
            'status',
            'retry_count',
            'response',
            'error_message',
            'delivered_at',
            'created_at',
            'updated_at',
        )


class NotificationLogDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ('id', 'delivered_at')


class NotificationLogListSerializer(serializers.ModelSerializer):
    notification = NotificationDropdownSerializer(read_only=True)
    recipient = NotificationRecipientDropdownSerializer(read_only=True)
    channel = NotificationChannelDropdownSerializer(read_only=True)
    status = NotificationStatusDropdownSerializer(read_only=True)

    class Meta:
        model = NotificationLog
        fields = (
            'id',
            'notification',
            'recipient',
            'channel',
            'status',
            'retry_count',
            'delivered_at',
        )
