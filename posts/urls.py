from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('<int:post_id>/', views.post_detail_view, name='detail'),
    path('<int:post_id>/sil/', views.post_delete_view, name='delete'),
    path('<int:post_id>/etkilesim/', views.interact_post, name='interact'),
    path('etiket/<str:hashtag_name>/', views.hashtag_posts_view, name='hashtag_posts'), # YENİ
    path('arama/', views.search_view, name='search'), # YENİ SATIR
]