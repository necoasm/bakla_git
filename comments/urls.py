from django.urls import path
from posts import views

app_name = 'comments'

urlpatterns = [
    path('<int:comment_id>/', views.comment_detail_view, name='detail'),
    path('<int:comment_id>/sil/', views.comment_delete_view, name='delete'),
    path('<int:comment_id>/etkilesim/', views.interact_comment_view, name='interact'),
]