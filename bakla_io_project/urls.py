from django.contrib import admin
from django.urls import path, include
from posts.views import home_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hesap/', include('users.urls')),
    path('bakla/', include('posts.urls', namespace='posts')),
    path('yanit/', include('comments.urls', namespace='comments')),
    path('ekonomi/', include('economy.urls', namespace='economy')),
    path('bildirimler/', include('notifications.urls', namespace='notifications')), # YENİ SATIR
    path('', home_view, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)