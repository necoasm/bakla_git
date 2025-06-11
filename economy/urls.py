from django.urls import path
from . import views

app_name = 'economy'

urlpatterns = [
    path('get-balance/', views.get_balance_view, name='get_balance'),
    path('transfer/<str:username>/', views.transfer_view, name='transfer'), # YENİ
]