from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from user.models import User
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

from .serializers import (
    NotificationPrioritySerializer,
    NotificationCategorySerializer,
    NotificationChannelSerializer,
    NotificationStatusSerializer,
    NotificationTemplateSerializer,
    NotificationSerializer,
    SystemNotificationSerializer,
    NotificationAttachmentSerializer,
    NotificationRecipientSerializer,
    NotificationPreferenceSerializer,
    NotificationQueueSerializer,
    NotificationLogSerializer
)

# ==========================================
# PAGINATION, SEARCHING & ORDERING HELPERS
# ==========================================

def paginate_queryset(request, queryset, serializer_class, context=None):
    page_size_param = request.query_params.get('page_size', 10)
    try:
        page_size = max(1, int(page_size_param))
    except ValueError:
        page_size = 10

    page_param = request.query_params.get('page', 1)
    paginator = Paginator(queryset, page_size)

    try:
        paginated_page = paginator.page(page_param)
    except PageNotAnInteger:
        paginated_page = paginator.page(1)
    except EmptyPage:
        paginated_page = paginator.page(paginator.num_pages)

    serializer = serializer_class(paginated_page.object_list, many=True, context=context)

    base_url = request.build_absolute_uri(request.path)
    next_link = None
    if paginated_page.has_next():
        next_link = f"{base_url}?page={paginated_page.next_page_number()}&page_size={page_size}"
    
    prev_link = None
    if paginated_page.has_previous():
        prev_link = f"{base_url}?page={paginated_page.previous_page_number()}&page_size={page_size}"

    return {
        "count": paginator.count,
        "next": next_link,
        "previous": prev_link,
        "results": serializer.data
    }


def apply_search(request, queryset, search_fields):
    search_query = request.query_params.get('search')
    if not search_query or not search_fields:
        return queryset

    query_filter = Q()
    for field in search_fields:
        query_filter |= Q(**{f"{field}__icontains": search_query})
    return queryset.filter(query_filter)


def apply_ordering(request, queryset, default="-created_at"):
    order_param = request.query_params.get('ordering', default)
    ordering_fields = [f.strip() for f in order_param.split(',')]
    sanitized_fields = []

    for field in ordering_fields:
        clean = field.lstrip('-')
        if clean.isidentifier() or '__' in clean:
            sanitized_fields.append(field)

    if sanitized_fields:
        try:
            return queryset.order_by(*sanitized_fields)
        except Exception:
            pass
    return queryset.order_by(default)


# ==========================================
# SOFT DELETE HELPER
# ==========================================

def soft_delete_instance(request, instance):
    try:
        instance.soft_delete(user=request.user)
    except Exception:
        try:
            instance.soft_delete()
        except Exception:
            instance.delete()


# ==========================================
# 1. MASTER VIEWSETS (ADMIN ONLY)
# ==========================================

class NotificationPriorityAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationPriority.objects.get(pk=pk)
        except NotificationPriority.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Priority not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationPrioritySerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationPriority.objects.all()
            queryset = apply_search(request, queryset, ['name', 'code', 'description'])
            queryset = apply_ordering(request, queryset, 'display_order')
            paginated_data = paginate_queryset(request, queryset, NotificationPrioritySerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationPrioritySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Priority not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationPrioritySerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Priority not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationPrioritySerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Priority not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Priority deleted successfully."}, status=status.HTTP_200_OK)


class NotificationCategoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationCategory.objects.get(pk=pk)
        except NotificationCategory.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationCategorySerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationCategory.objects.all()
            queryset = apply_search(request, queryset, ['name', 'code', 'description'])
            queryset = apply_ordering(request, queryset, 'name')
            paginated_data = paginate_queryset(request, queryset, NotificationCategorySerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationCategorySerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationCategorySerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Category deleted successfully."}, status=status.HTTP_200_OK)


class NotificationChannelAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationChannel.objects.get(pk=pk)
        except NotificationChannel.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Channel not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationChannelSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationChannel.objects.all()
            queryset = apply_search(request, queryset, ['name', 'code', 'description'])
            queryset = apply_ordering(request, queryset, 'display_order')
            paginated_data = paginate_queryset(request, queryset, NotificationChannelSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationChannelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Channel not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationChannelSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Channel not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationChannelSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Channel not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Channel deleted successfully."}, status=status.HTTP_200_OK)


class NotificationStatusAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationStatus.objects.get(pk=pk)
        except NotificationStatus.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Status not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationStatusSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationStatus.objects.all()
            queryset = apply_search(request, queryset, ['name', 'code', 'description'])
            queryset = apply_ordering(request, queryset, 'display_order')
            paginated_data = paginate_queryset(request, queryset, NotificationStatusSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Status not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationStatusSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Status not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationStatusSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Status not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Status deleted successfully."}, status=status.HTTP_200_OK)


class NotificationTemplateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationTemplate.objects.get(pk=pk)
        except NotificationTemplate.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationTemplateSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationTemplate.objects.all()
            category = request.query_params.get('category')
            priority = request.query_params.get('priority')
            is_active = request.query_params.get('is_active')

            if category:
                queryset = queryset.filter(category_id=category)
            if priority:
                queryset = queryset.filter(priority_id=priority)
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')

            queryset = apply_search(request, queryset, ['code', 'title', 'body'])
            queryset = apply_ordering(request, queryset, '-created_at')
            paginated_data = paginate_queryset(request, queryset, NotificationTemplateSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationTemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationTemplateSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationTemplateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Template deleted successfully."}, status=status.HTTP_200_OK)


# ==========================================
# 2. NOTIFICATION MANAGEMENT VIEWSETS
# ==========================================

class NotificationAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = Notification.objects.all()
            queryset = apply_search(request, queryset, ['title', 'message'])
            queryset = apply_ordering(request, queryset, '-created_at')
            paginated_data = paginate_queryset(request, queryset, NotificationSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        recipients_ids = request.data.get('recipients', [])
        if not recipients_ids:
            return Response({"recipients": ["At least one recipient user ID is required."]}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(id__in=recipients_ids)
        if not users.exists():
            return Response({"recipients": ["No valid users found for the provided IDs."]}, status=status.HTTP_400_BAD_REQUEST)

        # Create notification record
        notification = serializer.save()

        # Create recipients
        for user in users:
            NotificationRecipient.objects.get_or_create(
                notification=notification,
                user=user
            )

        # Retrieve channels based on is_system_generated
        if notification.is_system_generated:
            channels = []
            for code in ['email', 'in-app']:
                channel_obj, _ = NotificationChannel.objects.get_or_create(
                    code=code,
                    defaults={'name': code.capitalize(), 'is_active': True}
                )
                if channel_obj.is_active:
                    channels.append(channel_obj)
        else:
            default_channel = NotificationChannel.objects.filter(is_default=True, is_active=True).first()
            if not default_channel:
                default_channel = NotificationChannel.objects.filter(is_active=True).first()
            channels = [default_channel] if default_channel else []

        status_obj = NotificationStatus.objects.filter(is_default=True, is_active=True).first()
        if not status_obj:
            status_obj, _ = NotificationStatus.objects.get_or_create(
                code='PENDING',
                defaults={'name': 'Pending', 'is_active': True, 'is_default': True}
            )

        # Create queue jobs
        if status_obj and channels:
            for user in users:
                for channel in channels:
                    NotificationQueue.objects.get_or_create(
                        notification=notification,
                        recipient=user,
                        channel=channel,
                        status=status_obj
                    )

        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PUT not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method PATCH not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Notification soft deleted successfully."}, status=status.HTTP_200_OK)


class NotificationAttachmentAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk):
        try:
            return NotificationAttachment.objects.get(pk=pk)
        except NotificationAttachment.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            instance = self._get_object(pk)
            if not instance:
                return Response({"error": "Attachment not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationAttachmentSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationAttachment.objects.all()
            paginated_data = paginate_queryset(request, queryset, NotificationAttachmentSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NotificationAttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            return Response({"error": "Method DELETE not allowed without pk"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self._get_object(pk)
        if not instance:
            return Response({"error": "Attachment not found."}, status=status.HTTP_404_NOT_FOUND)
        soft_delete_instance(request, instance)
        return Response({"message": "Attachment soft deleted successfully."}, status=status.HTTP_200_OK)


# ==========================================
# 3. USER NOTIFICATION VIEWSETS
# ==========================================

class MyNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        user = request.user
        if pk is not None:
            try:
                recipient = NotificationRecipient.objects.get(pk=pk, user=user)
            except NotificationRecipient.DoesNotExist:
                return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = NotificationRecipientSerializer(recipient)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationRecipient.objects.filter(user=user).select_related(
                'notification', 'notification__category', 'notification__priority'
            )

            is_read = request.query_params.get('is_read')
            is_seen = request.query_params.get('is_seen')
            is_archived = request.query_params.get('is_archived')
            category = request.query_params.get('category')
            priority = request.query_params.get('priority')

            if is_read is not None:
                queryset = queryset.filter(is_read=is_read.lower() == 'true')
            if is_seen is not None:
                queryset = queryset.filter(is_seen=is_seen.lower() == 'true')
            if is_archived is not None:
                queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
            if category:
                queryset = queryset.filter(notification__category_id=category)
            if priority:
                queryset = queryset.filter(notification__priority_id=priority)

            unread_count = NotificationRecipient.objects.filter(
                user=user, is_read=False
            ).count()

            paginated_data = paginate_queryset(request, queryset, NotificationRecipientSerializer)
            paginated_data['unread_count'] = unread_count
            return Response(paginated_data, status=status.HTTP_200_OK)

    def patch(self, request, pk=None):
        user = request.user
        if pk is None:
            # Bulk action (mark all read or archive all)
            action_type = request.data.get('action') or request.query_params.get('action')
            if action_type == 'mark_all_read':
                NotificationRecipient.objects.filter(user=user, is_read=False).update(
                    is_read=True, read_at=timezone.now()
                )
                return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)
            elif action_type == 'archive_all':
                NotificationRecipient.objects.filter(user=user, is_archived=False).update(
                    is_archived=True, archived_at=timezone.now()
                )
                return Response({"message": "All notifications archived successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Bulk action not specified or invalid."}, status=status.HTTP_400_BAD_REQUEST)

        # Single item actions: mark read, unread, seen, archive
        try:
            recipient = NotificationRecipient.objects.get(pk=pk, user=user)
        except NotificationRecipient.DoesNotExist:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

        action_type = request.data.get('action') or request.query_params.get('action')
        if action_type == 'read':
            recipient.is_read = True
            recipient.read_at = timezone.now()
        elif action_type == 'unread':
            recipient.is_read = False
            recipient.read_at = None
        elif action_type == 'seen':
            recipient.is_seen = True
            recipient.seen_at = timezone.now()
        elif action_type == 'archive':
            recipient.is_archived = True
            recipient.archived_at = timezone.now()
        else:
            # standard partial update
            serializer = NotificationRecipientSerializer(recipient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        recipient.save()
        return Response({"message": f"Notification marked as {action_type} successfully."}, status=status.HTTP_200_OK)


class NotificationPreferenceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        pref, created = NotificationPreference.objects.get_or_create(user=user)
        return pref

    def get(self, request):
        pref = self.get_object(request.user)
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        pref = self.get_object(request.user)
        serializer = NotificationPreferenceSerializer(pref, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        pref = self.get_object(request.user)
        serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 4. QUEUE & DELIVERY VIEWSETS
# ==========================================

class NotificationQueueAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk is not None:
            try:
                queue_item = NotificationQueue.objects.get(pk=pk)
            except NotificationQueue.DoesNotExist:
                return Response({"error": "Queue item not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationQueueSerializer(queue_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationQueue.objects.all()
            status_id = request.query_params.get('status')
            channel = request.query_params.get('channel')
            recipient = request.query_params.get('recipient')

            if status_id:
                queryset = queryset.filter(status_id=status_id)
            if channel:
                queryset = queryset.filter(channel_id=channel)
            if recipient:
                queryset = queryset.filter(recipient_id=recipient)

            paginated_data = paginate_queryset(request, queryset, NotificationQueueSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)

    def post(self, request, pk=None):
        if pk is not None:
            # Retry failed attempt
            try:
                queue_item = NotificationQueue.objects.get(pk=pk)
            except NotificationQueue.DoesNotExist:
                return Response({"error": "Queue item not found."}, status=status.HTTP_404_NOT_FOUND)

            pending_status = NotificationStatus.objects.filter(code='PENDING').first()
            if not pending_status:
                pending_status = NotificationStatus.objects.filter(is_default=True).first()

            queue_item.retry_count = 0
            if pending_status:
                queue_item.status = pending_status
            queue_item.save()

            return Response({"message": "Queued item reset for delivery retry."}, status=status.HTTP_200_OK)
        
        # Standard create
        serializer = NotificationQueueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationLogAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk is not None:
            try:
                log_item = NotificationLog.objects.get(pk=pk)
            except NotificationLog.DoesNotExist:
                return Response({"error": "Log not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = NotificationLogSerializer(log_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = NotificationLog.objects.all()
            status_id = request.query_params.get('status')
            channel = request.query_params.get('channel')
            recipient_id = request.query_params.get('recipient_id')

            if status_id:
                queryset = queryset.filter(status_id=status_id)
            if channel:
                queryset = queryset.filter(channel_id=channel)
            if recipient_id:
                queryset = queryset.filter(recipient__user_id=recipient_id)

            paginated_data = paginate_queryset(request, queryset, NotificationLogSerializer)
            return Response(paginated_data, status=status.HTTP_200_OK)


class SystemNotificationAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = SystemNotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        recipients_ids = serializer.validated_data.pop('recipients', [])
        template_code = serializer.validated_data.pop('template_code', None)
        title = serializer.validated_data.get('title')
        message = serializer.validated_data.get('message')
        metadata = serializer.validated_data.get('metadata', {})
        template_obj = None

        if template_code:
            template_obj = NotificationTemplate.objects.filter(code=template_code, is_active=True).first()
            if template_obj:
                try:
                    title = template_obj.title.format(**metadata)
                    message = template_obj.body.format(**metadata)
                    serializer.validated_data['title'] = title
                    serializer.validated_data['message'] = message
                    
                    if template_obj.category and not serializer.validated_data.get('category'):
                        serializer.validated_data['category'] = template_obj.category
                    if template_obj.priority and not serializer.validated_data.get('priority'):
                        serializer.validated_data['priority'] = template_obj.priority
                except KeyError as e:
                    return Response({"error": f"Missing variable in metadata for template: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"template_code": ["Invalid or inactive template code."]}, status=status.HTTP_400_BAD_REQUEST)
        
        if not title or not message:
            return Response({"error": "Either (title and message) or a valid template_code must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(id__in=recipients_ids)
        if not users.exists():
            return Response({"recipients": ["No valid users found for the provided IDs."]}, status=status.HTTP_400_BAD_REQUEST)

        # Force is_system_generated to True and save template if used
        save_kwargs = {'is_system_generated': True}
        if template_obj:
            save_kwargs['template'] = template_obj
            
        notification = serializer.save(**save_kwargs)

        # Create recipient inbox mappings
        for user in users:
            NotificationRecipient.objects.get_or_create(
                notification=notification,
                user=user
            )

        # Create/retrieve channels for email and in-app
        channels = []
        for code in ['email', 'in-app']:
            channel_obj, _ = NotificationChannel.objects.get_or_create(
                code=code,
                defaults={'name': code.capitalize(), 'is_active': True}
            )
            if channel_obj.is_active:
                channels.append(channel_obj)

        # Retrieve default status for queueing
        status_obj = NotificationStatus.objects.filter(is_default=True, is_active=True).first()
        if not status_obj:
            status_obj, _ = NotificationStatus.objects.get_or_create(
                code='PENDING',
                defaults={'name': 'Pending', 'is_active': True, 'is_default': True}
            )

        # Create queue jobs
        if status_obj and channels:
            for user in users:
                for channel in channels:
                    NotificationQueue.objects.get_or_create(
                        notification=notification,
                        recipient=user,
                        channel=channel,
                        status=status_obj
                    )

        return Response({
            "notification_id": notification.id,
            "message": "System notification created successfully."
        }, status=status.HTTP_201_CREATED)

