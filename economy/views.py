from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from users.models import User
from .models import Wallet

@login_required
def get_balance_view(request):
    """
    Giriş yapmış kullanıcının cüzdanındaki güncel bakiye bilgisini
    JSON formatında döndürür.
    """
    try:
        balance = request.user.wallet.balance
        return JsonResponse({'success': True, 'balance': balance})
    except AttributeError:
        return JsonResponse({'success': False, 'error': 'Wallet not found'}, status=404)

@login_required
def transfer_view(request, username):
    recipient_user = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        try:
            # Formdan gelen 'amount' değerini al ve integer'a çevir
            amount = int(request.POST.get('amount'))
            
            # Miktar pozitif mi diye kontrol et
            if amount <= 0:
                messages.error(request, "Lütfen pozitif bir miktar girin.")
                return redirect('profile', username=username)

            sender_wallet = request.user.wallet
            
            # Gönderenin bakiyesi yeterli mi diye kontrol et
            if sender_wallet.balance < amount:
                messages.error(request, "Yetersiz bakiye!")
                return redirect('profile', username=username)

            recipient_wallet = recipient_user.wallet
            
            # Transfer işlemini yap
            sender_wallet.balance -= amount
            recipient_wallet.balance += amount
            
            # Değişiklikleri veritabanına kaydet
            sender_wallet.save()
            recipient_wallet.save()
            
            messages.success(request, f"{recipient_user.username} kullanıcısına başarıyla {amount} harf gönderdiniz.")
            # TODO: Bildirim gönder
            return redirect('profile', username=username)

        except (ValueError, TypeError):
            # Eğer 'amount' bir sayı değilse veya boşsa
            messages.error(request, "Geçersiz miktar girdiniz.")
            return redirect('profile', username=username)
    
    # GET isteği için bir şey yapmıyoruz, formu gösteren sayfaya geri yönlendir
    return redirect('profile', username=username)