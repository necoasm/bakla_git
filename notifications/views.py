from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification

@login_required
def notification_list_view(request):
    all_notifications = request.user.notifications.all().order_by('is_read', '-created_at')
    
    paginator = Paginator(all_notifications, 15)
    page_number = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page_number)

    # --- DÜZELTİLMİŞ MANTIK ---
    # 1. O anki sayfada bulunan ve okunmamış olan bildirimlerin ID'lerini bir liste olarak al.
    unread_notification_ids = [
        notification.id for notification in notifications_page.object_list if not notification.is_read
    ]

    # 2. Eğer böyle bildirimler varsa, ana QuerySet'i bu ID'lere göre filtreleyip güncelle.
    # Bu, "dilimlenmiş sorguyu filtreleme" hatasını önler.
    if unread_notification_ids:
        request.user.notifications.filter(id__in=unread_notification_ids).update(is_read=True)
    # --- DÜZELTME SONU ---

    # HTMX isteği gelirse, sadece bildirim listesini içeren parçayı gönder
    if request.htmx:
        return render(request, 'notifications/partials/notification_list_partial.html', {'notifications': notifications_page})

    context = {
        'notifications': notifications_page
    }
    return render(request, 'notifications/notification_list.html', context)