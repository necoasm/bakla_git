# users/urls.py
from django.urls import path
from . import views

# app_name='users' satırını siliyoruz, namespace'i ana urls.py'de yöneteceğiz.

urlpatterns = [
    path('kayit/', views.register_view, name='register'),
    path('giris/', views.login_view, name='login'),
    path('cikis/', views.logout_view, name='logout'),
    path('duzenle/', views.profile_edit_view, name='profile_edit'), # YENİ SATIR

# Yeni profil sayfası URL'i
    # <str:username> kısmı, URL'deki metni yakalayıp 'username' değişkeni olarak view'e gönderir.
    path('<str:username>/', views.profile_view, name='profile'),
    # Yeni Takip/Bırakma URL'leri
    path('<str:username>/takip_et/', views.follow_user, name='follow'),
    path('<str:username>/takipten_cik/', views.unfollow_user, name='unfollow'),

    path('<str:username>/takipciler/', views.follower_list_view, name='followers'),
    path('<str:username>/takip-edilenler/', views.following_list_view, name='following'),


]