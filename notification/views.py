import logging
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, QuerySet

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from user.models import User
from .models import (
    NotificationCategory,
    NotificationPriority,
    NotificationChannel,
    NotificationStatus,
    NotificationTemplate,
    Notification,
    NotificationRecipient,
    NotificationPreference,
    NotificationAttachment,
    NotificationQueue,
    NotificationLog,
)
from .serializers import *
from .services import NotificationService
from .permissions import IsAdminOrReadOnly

logger = logging.getLogger(__name__)


# ==========================================
# RESPONSE HELPERS
# ==========================================

def success_response(message: str, data: Optional[Dict[str, Any]] = None, status_code: int = status.HTTP_200_OK) -> Response:
    """Standardized API success wrapper."""
    return Response({
        "success": True,
        "message": message,
        "data": data or {}
    }, status=status_code)


def error_response(message: str, errors: Optional[Dict[str, Any]] = None, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """Standardized API error wrapper."""
    return Response({
        "success": False,
        "message": message,
        "errors": errors or {}
    }, status=status_code)


# ==========================================
# PAGINATION, SEARCHING & ORDERING HELPERS
# ==========================================

def paginate_queryset(request, queryset: QuerySet, serializer_class, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Manually paginates a queryset for APIViews, returning DRF-standard layout inside data.
    """
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

    # Reconstruct absolute navigation URIs
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


def apply_search(request, queryset: QuerySet, search_fields: List[str]) -> QuerySet:
    """Applies icontains filters to the queryset across designated lookup fields."""
    search_query = request.query_params.get('search')
    if not search_query or not search_fields:
        return queryset

    query_filter = Q()
    for field in search_fields:
        query_filter |= Q(**{f"{field}__icontains": search_query})
    return queryset.filter(query_filter)


def apply_ordering(request, queryset: QuerySet, default: str = "-created_at") -> QuerySet:
    """Applies sorting logic validating the query parameters."""
    order_param = request.query_params.get('ordering', default)
    
    # Map friendly filter words to db paths
    mapping = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'priority': 'priority__display_order',
        '-priority': '-priority__display_order',
        'created_date': 'created_at',
        '-created_date': '-created_at',
        'updated_date': 'updated_at',
        '-updated_date': '-updated_at',
    }

    ordering_fields = [f.strip() for f in order_param.split(',')]
    sanitized_fields = []

    for field in ordering_fields:
        mapped_field = mapping.get(field, field)
        clean = mapped_field.lstrip('-')
        if clean.isidentifier() or '__' in clean:
            sanitized_fields.append(mapped_field)

    if sanitized_fields:
        try:
            return queryset.order_by(*sanitized_fields)
        except Exception:
            pass
    return queryset.order_by(default)


def apply_date_range(request, queryset: QuerySet, date_field: str = "created_at") -> QuerySet:
    """Filters data range using start_date and end_date constraints."""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    filters = {}
    if start_date:
        filters[f"{date_field}__gte"] = start_date
    if end_date:
        filters[f"{date_field}__lte"] = end_date
    if filters:
        try:
            return queryset.filter(**filters)
        except Exception:
            pass
    return queryset


# ==========================================
# 1. NOTIFICATION CATEGORY VIEWS
# ==========================================

class NotificationCategoryListCreateAPIView(APIView):
    """List categories or create a new category."""
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request) -> Response:
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted == 'true':
            queryset = NotificationCategory.all_objects.filter(is_deleted=True)
        elif is_deleted == 'all':
            queryset = NotificationCategory.all_objects.all()
        else:
            queryset = NotificationCategory.objects.all()

        queryset = apply_search(request, queryset, ['name', 'code', 'description'])
        queryset = apply_ordering(request, queryset, 'name')
        
        paginated_data = paginate_queryset(request, queryset, NotificationCategoryListSerializer)
        return success_response("Categories retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        serializer = NotificationCategoryInputSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            output = NotificationCategoryOutputSerializer(category)
            return success_response("Category created successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)


class NotificationCategoryDetailAPIView(APIView):
    """Retrieve, update, or soft-delete a category."""
    permission_classes = [IsAdminOrReadOnly]

    def _get_object(self, pk: int) -> NotificationCategory:
        try:
            return NotificationCategory.all_objects.get(pk=pk)
        except NotificationCategory.DoesNotExist as e:
            raise ObjectDoesNotExist("Category not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            category = self._get_object(pk)
            serializer = NotificationCategoryOutputSerializer(category)
            return success_response("Category details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            category = self._get_object(pk)
            serializer = NotificationCategoryInputSerializer(category, data=request.data)
            if serializer.is_valid():
                updated_category = serializer.save()
                output = NotificationCategoryOutputSerializer(updated_category)
                return success_response("Category updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            category = self._get_object(pk)
            serializer = NotificationCategoryInputSerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                updated_category = serializer.save()
                output = NotificationCategoryOutputSerializer(updated_category)
                return success_response("Category patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            category = self._get_object(pk)
            category.soft_delete(user=request.user)
            return success_response("Category soft-deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 2. NOTIFICATION PRIORITY VIEWS
# ==========================================

class NotificationPriorityListCreateAPIView(APIView):
    """List priorities or create a new priority."""
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request) -> Response:
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted == 'true':
            queryset = NotificationPriority.all_objects.filter(is_deleted=True)
        elif is_deleted == 'all':
            queryset = NotificationPriority.all_objects.all()
        else:
            queryset = NotificationPriority.objects.all()

        queryset = apply_search(request, queryset, ['name', 'code', 'description'])
        queryset = apply_ordering(request, queryset, 'display_order')

        paginated_data = paginate_queryset(request, queryset, NotificationPriorityListSerializer)
        return success_response("Priorities retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        serializer = NotificationPriorityInputSerializer(data=request.data)
        if serializer.is_valid():
            priority = serializer.save()
            output = NotificationPriorityOutputSerializer(priority)
            return success_response("Priority created successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)


class NotificationPriorityDetailAPIView(APIView):
    """Retrieve, update, or soft-delete a priority."""
    permission_classes = [IsAdminOrReadOnly]

    def _get_object(self, pk: int) -> NotificationPriority:
        try:
            return NotificationPriority.all_objects.get(pk=pk)
        except NotificationPriority.DoesNotExist as e:
            raise ObjectDoesNotExist("Priority not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            priority = self._get_object(pk)
            serializer = NotificationPriorityOutputSerializer(priority)
            return success_response("Priority details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_444_NOT_FOUND if False else status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            priority = self._get_object(pk)
            serializer = NotificationPriorityInputSerializer(priority, data=request.data)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationPriorityOutputSerializer(updated)
                return success_response("Priority updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            priority = self._get_object(pk)
            serializer = NotificationPriorityInputSerializer(priority, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationPriorityOutputSerializer(updated)
                return success_response("Priority patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            priority = self._get_object(pk)
            priority.soft_delete(user=request.user)
            return success_response("Priority soft-deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_444_NOT_FOUND if False else status.HTTP_404_NOT_FOUND)


# ==========================================
# 3. NOTIFICATION CHANNEL VIEWS
# ==========================================

class NotificationChannelListCreateAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request) -> Response:
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted == 'true':
            queryset = NotificationChannel.all_objects.filter(is_deleted=True)
        elif is_deleted == 'all':
            queryset = NotificationChannel.all_objects.all()
        else:
            queryset = NotificationChannel.objects.all()

        queryset = apply_search(request, queryset, ['name', 'code'])
        queryset = apply_ordering(request, queryset, 'display_order')

        paginated_data = paginate_queryset(request, queryset, NotificationChannelListSerializer)
        return success_response("Channels retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        serializer = NotificationChannelInputSerializer(data=request.data)
        if serializer.is_valid():
            channel = serializer.save()
            output = NotificationChannelOutputSerializer(channel)
            return success_response("Channel created successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)


class NotificationChannelDetailAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def _get_object(self, pk: int) -> NotificationChannel:
        try:
            return NotificationChannel.all_objects.get(pk=pk)
        except NotificationChannel.DoesNotExist as e:
            raise ObjectDoesNotExist("Channel not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            channel = self._get_object(pk)
            serializer = NotificationChannelOutputSerializer(channel)
            return success_response("Channel details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            channel = self._get_object(pk)
            serializer = NotificationChannelInputSerializer(channel, data=request.data)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationChannelOutputSerializer(updated)
                return success_response("Channel updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_444_NOT_FOUND if False else status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            channel = self._get_object(pk)
            serializer = NotificationChannelInputSerializer(channel, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationChannelOutputSerializer(updated)
                return success_response("Channel patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            channel = self._get_object(pk)
            channel.soft_delete(user=request.user)
            return success_response("Channel soft-deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 4. NOTIFICATION STATUS VIEWS
# ==========================================

class NotificationStatusListCreateAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request) -> Response:
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted == 'true':
            queryset = NotificationStatus.all_objects.filter(is_deleted=True)
        elif is_deleted == 'all':
            queryset = NotificationStatus.all_objects.all()
        else:
            queryset = NotificationStatus.objects.all()

        queryset = apply_search(request, queryset, ['name', 'code'])
        queryset = apply_ordering(request, queryset, 'display_order')

        paginated_data = paginate_queryset(request, queryset, NotificationStatusListSerializer)
        return success_response("Statuses retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        serializer = NotificationStatusInputSerializer(data=request.data)
        if serializer.is_valid():
            status_obj = serializer.save()
            output = NotificationStatusOutputSerializer(status_obj)
            return success_response("Status created successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)


class NotificationStatusDetailAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def _get_object(self, pk: int) -> NotificationStatus:
        try:
            return NotificationStatus.all_objects.get(pk=pk)
        except NotificationStatus.DoesNotExist as e:
            raise ObjectDoesNotExist("Status not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            status_obj = self._get_object(pk)
            serializer = NotificationStatusOutputSerializer(status_obj)
            return success_response("Status details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            status_obj = self._get_object(pk)
            serializer = NotificationStatusInputSerializer(status_obj, data=request.data)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationStatusOutputSerializer(updated)
                return success_response("Status updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            status_obj = self._get_object(pk)
            serializer = NotificationStatusInputSerializer(status_obj, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationStatusOutputSerializer(updated)
                return success_response("Status patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            status_obj = self._get_object(pk)
            status_obj.soft_delete(user=request.user)
            return success_response("Status soft-deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 5. NOTIFICATION TEMPLATE VIEWS
# ==========================================

class NotificationTemplateListCreateAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request) -> Response:
        queryset = NotificationTemplate.objects.select_related('category', 'priority').all()

        # Filters
        is_active = request.query_params.get('is_active')
        if is_active in ['true', 'false']:
            queryset = queryset.filter(is_active=(is_active == 'true'))
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        priority_id = request.query_params.get('priority')
        if priority_id:
            queryset = queryset.filter(priority_id=priority_id)

        queryset = apply_search(request, queryset, ['code', 'title', 'body'])
        queryset = apply_ordering(request, queryset, '-created_at')

        paginated_data = paginate_queryset(request, queryset, NotificationTemplateListSerializer)
        return success_response("Templates retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        serializer = NotificationTemplateInputSerializer(data=request.data)
        if serializer.is_valid():
            template = serializer.save()
            output = NotificationTemplateOutputSerializer(template)
            return success_response("Template created successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)


class NotificationTemplateDetailAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def _get_object(self, pk: int) -> NotificationTemplate:
        try:
            return NotificationTemplate.objects.select_related('category', 'priority').get(pk=pk)
        except NotificationTemplate.DoesNotExist as e:
            raise ObjectDoesNotExist("Template not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            template = self._get_object(pk)
            serializer = NotificationTemplateOutputSerializer(template)
            return success_response("Template details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            template = self._get_object(pk)
            serializer = NotificationTemplateInputSerializer(template, data=request.data)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationTemplateOutputSerializer(updated)
                return success_response("Template updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_444_NOT_FOUND if False else status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            template = self._get_object(pk)
            serializer = NotificationTemplateInputSerializer(template, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationTemplateOutputSerializer(updated)
                return success_response("Template patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            template = self._get_object(pk)
            template.delete()  # Template has no SoftDeleteMixin in models
            return success_response("Template deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 6. CORE NOTIFICATION VIEWS
# ==========================================

class NotificationListCreateAPIView(APIView):
    """Administrative creation and index lookup of all Notification logs."""
    permission_classes = [IsAdminUser]

    def get(self, request) -> Response:
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted == 'true':
            queryset = Notification.all_objects.filter(is_deleted=True)
        elif is_deleted == 'all':
            queryset = Notification.all_objects.all()
        else:
            queryset = Notification.objects.all()

        queryset = queryset.select_related('category', 'priority', 'template')

        # Complex Filters
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        priority_id = request.query_params.get('priority')
        if priority_id:
            queryset = queryset.filter(priority_id=priority_id)
        is_system = request.query_params.get('is_system_generated')
        if is_system in ['true', 'false']:
            queryset = queryset.filter(is_system_generated=(is_system == 'true'))

        # Filter by recipient user id
        recipient_id = request.query_params.get('recipient_id')
        if recipient_id:
            queryset = queryset.filter(recipients__user_id=recipient_id)

        # Filter by sender user id (deleted_by contains auditing information)
        sender_id = request.query_params.get('sender_id')
        if sender_id:
            queryset = queryset.filter(deleted_by_id=sender_id)

        queryset = apply_date_range(request, queryset, 'created_at')
        queryset = apply_search(request, queryset, ['title', 'message', 'metadata', 'template__code'])
        queryset = apply_ordering(request, queryset, '-created_at')

        paginated_data = paginate_queryset(request, queryset, NotificationListSerializer)
        return success_response("Notifications retrieved successfully.", paginated_data)

    def post(self, request):
        serializer = NotificationInputSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                "Validation failed.",
                serializer.errors
            )

        recipient_ids = request.data.get("recipients", [])

        if not recipient_ids:
            return error_response(
                "Recipients are required.",
                {"recipients": ["This field is required."]}
            )

        users = list(
            User.objects.filter(
                id__in=recipient_ids,
                #is_active=True
            )
        )

        if not users:
            return error_response(
                "No valid recipients found."
            )

        try:

            service = NotificationService()

            notification = service.send_notification(

                recipients=users,

                category=serializer.validated_data["category"],

                priority=serializer.validated_data["priority"],

                template=serializer.validated_data.get("template"),

                title=serializer.validated_data["title"],

                message=serializer.validated_data["message"],

                metadata=serializer.validated_data.get("metadata"),

                action_url=serializer.validated_data.get("action_url"),

                icon=serializer.validated_data.get("icon"),

                scheduled_at=request.data.get("scheduled_at"),

                is_system_generated=serializer.validated_data.get(
                    "is_system_generated",
                    True,
                ),
            )

            return success_response(
                "Notification created successfully.",
                NotificationOutputSerializer(notification).data,
                status.HTTP_201_CREATED,
            )

        except Exception as e:

            logger.exception(e)

            return error_response(str(e))

class NotificationDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    def _get_object(self, pk: int) -> Notification:
        try:
            return Notification.all_objects.select_related('category', 'priority', 'template').get(pk=pk)
        except Notification.DoesNotExist as e:
            raise ObjectDoesNotExist("Notification record not found.") from e

    def get(self, request, pk: int) -> Response:
        try:
            notification = self._get_object(pk)
            serializer = NotificationOutputSerializer(notification)
            return success_response("Notification details retrieved.", serializer.data)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk: int) -> Response:
        try:
            notification = self._get_object(pk)
            serializer = NotificationInputSerializer(notification, data=request.data)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationOutputSerializer(updated)
                return success_response("Notification updated successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: int) -> Response:
        try:
            notification = self._get_object(pk)
            serializer = NotificationInputSerializer(notification, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                output = NotificationOutputSerializer(updated)
                return success_response("Notification patched successfully.", output.data)
            return error_response("Validation failed.", serializer.errors)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk: int) -> Response:
        try:
            notification = self._get_object(pk)
            notification.soft_delete(user=request.user)
            return success_response("Notification soft-deleted successfully.")
        except ObjectDoesNotExist as e:
            return error_response(str(e), status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 7. USER NOTIFICATION ENDPOINTS
# ==========================================

class MyNotificationAPIView(APIView):
    """Fetch notifications bound to the logged-in recipient user."""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        user = request.user
        queryset = NotificationRecipient.objects.filter(user=user, is_deleted=False).select_related(
            'notification', 'notification__category', 'notification__priority'
        )

        # Filters
        is_read = request.query_params.get('is_read')
        if is_read in ['true', 'false']:
            queryset = queryset.filter(is_read=(is_read == 'true'))

        is_seen = request.query_params.get('is_seen')
        if is_seen in ['true', 'false']:
            queryset = queryset.filter(is_seen=(is_seen == 'true'))

        is_archived = request.query_params.get('is_archived')
        if is_archived in ['true', 'false']:
            queryset = queryset.filter(is_archived=(is_archived == 'true'))

        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(notification__category_id=category_id)

        priority_id = request.query_params.get('priority')
        if priority_id:
            queryset = queryset.filter(notification__priority_id=priority_id)

        queryset = apply_search(request, queryset, ['notification__title', 'notification__message'])
        queryset = apply_ordering(request, queryset, '-created_at')

        # Dynamic live counts
        unread_count = NotificationRecipient.objects.filter(user=user, is_read=False, is_deleted=False).count()

        paginated_data = paginate_queryset(request, queryset, NotificationRecipientListSerializer)
        paginated_data['unread_count'] = unread_count

        return success_response("My notifications retrieved successfully.", paginated_data)


class MarkNotificationReadAPIView(APIView):
    """Mark a recipient notification as read."""
    permission_classes = [IsAuthenticated]

    def patch(self, request) -> Response:
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return error_response("notification_id is required in body.")

        try:
            # Pull recipient matching user
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user,
                is_deleted=False
            )
            
            service = NotificationService()
            service.mark_as_read(recipient.id, request.user)
            
            return success_response("Notification marked as read successfully.")
        except ObjectDoesNotExist:
            return error_response("Notification record not found.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(f"Failed to update status: {str(e)}")


class MarkNotificationSeenAPIView(APIView):
    """Mark a recipient notification as seen."""
    permission_classes = [IsAuthenticated]

    def patch(self, request) -> Response:
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return error_response("notification_id is required in body.")

        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user,
                is_deleted=False
            )
            
            service = NotificationService()
            service.mark_as_seen(recipient.id, request.user)
            
            return success_response("Notification marked as seen successfully.")
        except ObjectDoesNotExist:
            return error_response("Notification record not found.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(f"Failed to update status: {str(e)}")


class ArchiveNotificationAPIView(APIView):
    """Archive a recipient notification."""
    permission_classes = [IsAuthenticated]

    def patch(self, request) -> Response:
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return error_response("notification_id is required in body.")

        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user,
                is_deleted=False
            )
            
            service = NotificationService()
            service.archive_notification(recipient.id, request.user)
            
            return success_response("Notification archived successfully.")
        except ObjectDoesNotExist:
            return error_response("Notification record not found.", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(f"Failed to archive notification: {str(e)}")


# ==========================================
# 8. PREFERENCES & ATTACHMENT VIEWS
# ==========================================

class NotificationPreferenceAPIView(APIView):
    """Retrieve or modify notification preferences for request.user."""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceOutputSerializer(pref)
        return success_response("Notification preferences retrieved.", serializer.data)

    def put(self, request) -> Response:
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceInputSerializer(pref, data=request.data)
        if serializer.is_valid():
            updated = serializer.save()
            output = NotificationPreferenceOutputSerializer(updated)
            return success_response("Notification preferences updated.", output.data)
        return error_response("Validation failed.", serializer.errors)

    def patch(self, request) -> Response:
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceInputSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            output = NotificationPreferenceOutputSerializer(updated)
            return success_response("Notification preferences updated.", output.data)
        return error_response("Validation failed.", serializer.errors)


class NotificationAttachmentAPIView(APIView):
    """Manage notification file attachments (Multipart uploads)."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request) -> Response:
        # Normal users only see attachments linked to notifications they received
        if request.user.is_staff:
            queryset = NotificationAttachment.objects.all()
        else:
            queryset = NotificationAttachment.objects.filter(
                notification__recipients__user=request.user,
                is_deleted=False
            )
        
        queryset = queryset.select_related('notification')
        queryset = apply_search(request, queryset, ['file_name', 'file_type'])
        queryset = apply_ordering(request, queryset, '-created_at')

        paginated_data = paginate_queryset(request, queryset, NotificationAttachmentListSerializer)
        return success_response("Attachments retrieved successfully.", paginated_data)

    def post(self, request) -> Response:
        file_obj = request.FILES.get('file')
        if not file_obj:
            return error_response("Validation failed.", {"file": "A multipart file upload is required."})

        # Validate maximum size of 15MB boundaries
        max_size_bytes = 15 * 1024 * 1024
        if file_obj.size > max_size_bytes:
            return error_response("Validation failed.", {"file": "Maximum file attachment size limit is 15MB."})

        serializer = NotificationAttachmentInputSerializer(data=request.data)
        if serializer.is_valid():
            attachment = serializer.save(file=file_obj)
            output = NotificationAttachmentOutputSerializer(attachment)
            return success_response("Attachment uploaded successfully.", output.data, status.HTTP_201_CREATED)
        return error_response("Validation failed.", serializer.errors)

    def delete(self, request) -> Response:
        attachment_id = request.data.get('attachment_id')
        if not attachment_id:
            return error_response("attachment_id is required in body.")

        try:
            if request.user.is_staff:
                attachment = NotificationAttachment.objects.get(id=attachment_id)
            else:
                attachment = NotificationAttachment.objects.get(
                    id=attachment_id,
                    notification__recipients__user=request.user
                )

            attachment.soft_delete(user=request.user)
            return success_response("Attachment soft-deleted successfully.")
        except ObjectDoesNotExist:
            return error_response("Attachment not found.", status_code=status.HTTP_404_NOT_FOUND)


# ==========================================
# 9. QUEUE & AUDIT LOG VIEWS (ADMIN ONLY)
# ==========================================

class NotificationQueueAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request) -> Response:
        queryset = NotificationQueue.objects.select_related('notification', 'recipient', 'channel', 'status').all()

        # Filters
        status_id = request.query_params.get('status')
        if status_id:
            queryset = queryset.filter(status_id=status_id)
        priority = request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        retry_count = request.query_params.get('retry_count')
        if retry_count:
            queryset = queryset.filter(retry_count=retry_count)

        queryset = apply_date_range(request, queryset, 'scheduled_at')
        queryset = apply_search(request, queryset, ['recipient__full_name', 'recipient__contact_no', 'celery_task_id', 'error_message'])
        queryset = apply_ordering(request, queryset, 'priority')

        paginated_data = paginate_queryset(request, queryset, NotificationQueueListSerializer)
        return success_response("Queue items retrieved successfully.", paginated_data)


class NotificationLogAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request) -> Response:
        queryset = NotificationLog.objects.select_related('notification', 'recipient', 'recipient__user', 'channel', 'status').all()

        # Filters
        channel_id = request.query_params.get('channel')
        if channel_id:
            queryset = queryset.filter(channel_id=channel_id)
        status_id = request.query_params.get('status')
        if status_id:
            queryset = queryset.filter(status_id=status_id)
        recipient_id = request.query_params.get('recipient_id')
        if recipient_id:
            queryset = queryset.filter(recipient__user_id=recipient_id)

        queryset = apply_date_range(request, queryset, 'created_at')
        queryset = apply_search(request, queryset, ['recipient__user__full_name', 'recipient__user__contact_no', 'error_message'])
        queryset = apply_ordering(request, queryset, '-created_at')

        paginated_data = paginate_queryset(request, queryset, NotificationLogListSerializer)
        return success_response("Notification log audit records retrieved.", paginated_data)
