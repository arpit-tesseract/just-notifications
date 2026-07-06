from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.urls import reverse
from .models import NotificationRecipient, NotificationRecipientStatus

@login_required
def notification_list_view(request):
    """Full page view of all notifications with pagination."""
    notifications_qs = NotificationRecipient.objects.filter(
        user=request.user, 
        channel='in_app'
    ).select_related('notification').order_by('-created_at')
    
    paginator = Paginator(notifications_qs, 10) # Show 15 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notification/notification_list.html', {'page_obj': page_obj})

@login_required
def notification_api_view(request):
    import time
    time.sleep(1) # Artificial delay for testing loader
    """API endpoint for infinite scrolling in the notification dropdown."""
    notifications_qs = NotificationRecipient.objects.filter(
        user=request.user, 
        channel='in_app'
    ).select_related('notification').order_by('-created_at')
    
    # Paginate by 2 items per page for testing
    paginator = Paginator(notifications_qs, 10) # Load 10 at a time for dropdown
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        return JsonResponse({'data': [], 'has_next': False})
        
    data = []
    for recipient in page_obj:
        from django.utils.timesince import timesince
        data.append({
            'id': recipient.pk,
            'title': recipient.notification.title,
            'content': recipient.notification.content,
            'icon': recipient.notification.icon,
            'icon_color': recipient.notification.icon_color,
            'time': f"{timesince(recipient.created_at)} ago",
            'is_read': recipient.status == NotificationRecipientStatus.READ
        })
        
    return JsonResponse({'data': data, 'has_next': page_obj.has_next()})

@login_required
def mark_notification_read(request, pk):
    print("Marking notification as read...")
    """Mark a single notification as read."""
    if request.method == "POST":
        from django.utils import timezone
        notification = get_object_or_404(NotificationRecipient, pk=pk, user=request.user)
        was_unread = (notification.status != NotificationRecipientStatus.READ)
        
        if was_unread:
            notification.status = NotificationRecipientStatus.READ
            notification.read_at = timezone.now()
            notification.save(update_fields=['status', 'read_at'])
            
        return JsonResponse({'status': 'success', 'was_unread': was_unread})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def mark_all_read(request):
    """Mark all unread notifications as read."""
    if request.method == "POST":
        NotificationRecipient.objects.filter(
            user=request.user,
            status=NotificationRecipientStatus.UNREAD
        ).update(status=NotificationRecipientStatus.READ)
        
        # If HTMX or Fetch, we could return 200 OK. 
        # For simplicity, redirect to the list view or referring page.
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('notification:list')
    return JsonResponse({'status': 'error'}, status=400)
