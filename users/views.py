from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User
from posts.models import Post
from economy.models import Wallet
from notifications.models import Notification
from posts.views import _get_posts_with_interactions

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    all_posts = Post.objects.filter(author=profile_user).select_related('author').annotate(
        comment_count=Count('comments')
    ).order_by('-created_at')

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)

    if request.htmx:
        posts_page = _get_posts_with_interactions(request, posts_page)
        return render(request, 'posts/partials/post_list.html', {'posts': posts_page})

    posts_page = _get_posts_with_interactions(request, posts_page)
    
    is_following = request.user.is_authenticated and request.user.following.filter(pk=profile_user.pk).exists()

    context = {
        'profile_user': profile_user,
        'posts': posts_page,
        'is_following': is_following,
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profilin başarıyla güncellendi.")
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def follow_user(request, username):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    user_to_follow = get_object_or_404(User, username=username)
    is_already_following = request.user.following.filter(pk=user_to_follow.pk).exists()
    
    new_balance = user_to_follow.wallet.balance # Mevcut bakiyeyi al

    if request.user != user_to_follow and not is_already_following:
        request.user.following.add(user_to_follow)
        try:
            followed_user_wallet = user_to_follow.wallet
            followed_user_wallet.balance += 250
            followed_user_wallet.save()
            new_balance = followed_user_wallet.balance # Yeni bakiyeyi ata
        except Wallet.DoesNotExist:
            pass
        
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            verb=Notification.NotificationType.FOLLOW
        )

    data = {
        'success': True,
        'follower_count': user_to_follow.follower_count,
        'is_following': True,
        'new_balance': new_balance, # YENİ: Yeni bakiyeyi cevaba ekle
    }
    return JsonResponse(data)

@login_required
def unfollow_user(request, username):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    user_to_unfollow = get_object_or_404(User, username=username)
    
    new_balance = user_to_unfollow.wallet.balance # Mevcut bakiyeyi al

    if request.user.following.filter(pk=user_to_unfollow.pk).exists():
        request.user.following.remove(user_to_unfollow)
        try:
            unfollowed_user_wallet = user_to_unfollow.wallet
            unfollowed_user_wallet.balance -= 250
            unfollowed_user_wallet.save()
            new_balance = unfollowed_user_wallet.balance # Yeni bakiyeyi ata
        except Wallet.DoesNotExist:
            pass

    data = {
        'success': True,
        'follower_count': user_to_unfollow.follower_count,
        'is_following': False,
        'new_balance': new_balance, # YENİ: Yeni bakiyeyi cevaba ekle
    }
    return JsonResponse(data)

# ... (diğer importlar) ...

def follower_list_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = profile_user.followers.all().select_related('wallet')

    paginator = Paginator(followers, 20) # Bu listelerde daha fazla kişi gösterebiliriz
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.htmx:
        return render(request, 'users/partials/user_list_partial.html', {'user_list': page_obj})

    context = {
        'profile_user': profile_user,
        'user_list': page_obj,
        'list_type': 'Takipçi'
    }
    return render(request, 'users/follow_list.html', context)


def following_list_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = profile_user.following.all().select_related('wallet')

    paginator = Paginator(following, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.htmx:
        return render(request, 'users/partials/user_list_partial.html', {'user_list': page_obj})

    context = {
        'profile_user': profile_user,
        'user_list': page_obj,
        'list_type': 'Takip Edilen'
    }
    return render(request, 'users/follow_list.html', context)

def _prepare_follow_list(request, user_list_queryset):
    """
    Yardımcı fonksiyon: Verilen bir kullanıcı listesindeki her bir kullanıcı için,
    giriş yapmış kullanıcının takip durumunu bir özellik olarak ekler.
    """
    if not request.user.is_authenticated:
        return user_list_queryset

    # Giriş yapmış kullanıcının takip ettiği kişilerin ID'lerini bir set olarak al (hızlı arama için)
    following_ids = set(request.user.following.values_list('id', flat=True))

    for user in user_list_queryset:
        user.is_followed_by_request_user = user.id in following_ids
    
    return user_list_queryset

def follower_list_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = profile_user.followers.all().select_related('wallet')

    paginator = Paginator(followers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Her bir takipçiye, bizim onu takip edip etmediğimiz bilgisini ekle
    page_obj.object_list = _prepare_follow_list(request, page_obj.object_list)

    if request.htmx:
        return render(request, 'users/partials/user_list_partial.html', {'user_list': page_obj})

    context = {
        'profile_user': profile_user,
        'user_list': page_obj,
        'list_type': 'Takipçi'
    }
    return render(request, 'users/follow_list.html', context)


def following_list_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = profile_user.following.all().select_related('wallet')

    paginator = Paginator(following, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Takip edilen her bir kişiye, bizim onu takip edip etmediğimiz bilgisini ekle
    page_obj.object_list = _prepare_follow_list(request, page_obj.object_list)

    if request.htmx:
        return render(request, 'users/partials/user_list_partial.html', {'user_list': page_obj})

    context = {
        'profile_user': profile_user,
        'user_list': page_obj,
        'list_type': 'Takip Edilen'
    }
    return render(request, 'users/follow_list.html', context)
