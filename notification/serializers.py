from rest_framework import serializers
from .models import NotificationRecipient, NotificationRecipientStatus


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed view of a single notification.
    """
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    icon_color = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationRecipient
        fields = ['id', 'title', 'content', 'icon', 'icon_color', 'is_read', 'created_at', 'read_at', 'channel']

    def get_title(self, obj):
        return obj.notification.title

    def get_content(self, obj):
        return obj.notification.content

    def get_icon(self, obj):
        return obj.notification.icon

    def get_icon_color(self, obj):
        return obj.notification.icon_color

    def get_is_read(self, obj):
        return obj.status == NotificationRecipientStatus.READ


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications.
    Often contains fewer fields than the detail serializer to optimize list views.
    """
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    icon_color = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    time = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationRecipient
        fields = ['id', 'title', 'content', 'icon', 'icon_color', 'is_read', 'time']

    def get_title(self, obj):
        return obj.notification.title

    def get_content(self, obj):
        return obj.notification.content

    def get_icon(self, obj):
        return obj.notification.icon

    def get_icon_color(self, obj):
        return obj.notification.icon_color

    def get_is_read(self, obj):
        return obj.status == NotificationRecipientStatus.READ

    def get_time(self, obj):
        from django.utils.timesince import timesince
        return f"{timesince(obj.created_at)} ago"
