from rest_framework import serializers
from .models import (
    NotificationPriority,
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
    NotificationTemplate,
    Notification,
    NotificationRecipient,
    NotificationPreference,
    NotificationAttachment,
    NotificationQueue,
    NotificationLog
)

class NotificationPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPriority
        fields = '__all__'


class NotificationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        fields = '__all__'


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = '__all__'


class NotificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatus
        fields = '__all__'


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Notification
        fields = '__all__'


class SystemNotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True
    )
    template_code = serializers.CharField(write_only=True, required=False)
    title = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

    class Meta:
        model = Notification
        fields = ['recipients', 'template_code', 'title', 'message', 'category', 'priority', 'action_url', 'icon', 'metadata']



class NotificationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationAttachment
        fields = '__all__'


class NotificationRecipientSerializer(serializers.ModelSerializer):
    notification_details = NotificationSerializer(source='notification', read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = '__all__'


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'


class NotificationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationQueue
        fields = '__all__'


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'
