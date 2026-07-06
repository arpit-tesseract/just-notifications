from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.utils import timezone
from django.core.paginator import Paginator
from .models import NotificationRecipient, NotificationRecipientStatus
from .serializers import NotificationListSerializer


class NotificationListView(views.APIView):
    """API endpoint for listing notifications with pagination."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        import time
        time.sleep(1) # Artificial delay for testing loader (from original view)
        
        notifications_qs = NotificationRecipient.objects.filter(
            user=request.user, 
            channel='in_app'
        ).select_related('notification').order_by('-created_at')
        
        paginator = Paginator(notifications_qs, 10)
        page_number = request.query_params.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            return Response({'data': [], 'has_next': False})
            
        serializer = NotificationListSerializer(page_obj, many=True)
        return Response({
            'data': serializer.data,
            'has_next': page_obj.has_next()
        })


class MarkNotificationReadView(views.APIView):
    """Mark a single notification as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            notification = NotificationRecipient.objects.get(pk=pk, user=request.user)
        except NotificationRecipient.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Notification not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        was_unread = (notification.status != NotificationRecipientStatus.READ)
        
        if was_unread:
            notification.status = NotificationRecipientStatus.READ
            notification.read_at = timezone.now()
            notification.save(update_fields=['status', 'read_at'])
            
        return Response({'status': 'success', 'was_unread': was_unread})


class MarkAllNotificationsReadView(views.APIView):
    """Mark all unread notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        updated_count = NotificationRecipient.objects.filter(
            user=request.user,
            status=NotificationRecipientStatus.UNREAD
        ).update(
            status=NotificationRecipientStatus.READ,
            read_at=timezone.now()
        )
        return Response({'status': 'success', 'updated_count': updated_count})
