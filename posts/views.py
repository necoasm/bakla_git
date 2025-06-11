from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from .models import Post, Interaction, Comment, CommentInteraction, Hashtag
from .forms import PostForm, CommentForm
from users.models import User
from economy.models import Wallet

def _get_posts_with_interactions(request, posts_queryset):
    """
    Tekrarlanan kodu azaltmak için yardımcı fonksiyon.
    Verilen bir post queryset'ine, kullanıcı etkileşimlerini ve mutlak URL'leri ekler.
    """
    if request.user.is_authenticated:
        user_interactions = Interaction.objects.filter(user=request.user, post__in=posts_queryset).values('post_id', 'interaction_type')
        interactions_map = {item['post_id']: item['interaction_type'] for item in user_interactions}
        for post in posts_queryset:
            post.user_interaction = interactions_map.get(post.id)
            post.absolute_url = request.build_absolute_uri(post.get_absolute_url())
    return posts_queryset

@login_required
def home_view(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            post_cost = len(content)
            wallet = request.user.wallet
            if post_cost > wallet.balance:
                messages.error(request, "İşlem reddedildi. Bu baklayı göndermek için yeterli harfiniz yok.")
                return redirect('home')
            wallet.balance -= post_cost
            wallet.save()
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, f"Bakla paylaşıldı! ({post_cost} harf kullanıldı)")
            return redirect('home')

    followed_users = request.user.following.all()
    post_filter = Q(author__in=followed_users) | Q(author=request.user)
    all_posts = Post.objects.filter(post_filter).select_related('author').annotate(comment_count=Count('comments')).distinct().order_by('-created_at')

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)

    if request.htmx:
        posts_page = _get_posts_with_interactions(request, posts_page)
        return render(request, 'posts/partials/post_list.html', {'posts': posts_page})

    posts_page = _get_posts_with_interactions(request, posts_page)
    
    followed_users_ids = list(followed_users.values_list('id', flat=True))
    all_user_ids_to_exclude = list(followed_users_ids) + [request.user.id]
    suggested_users = User.objects.exclude(id__in=all_user_ids_to_exclude)[:3]

    popular_hashtags = Hashtag.objects.annotate(num_posts=Count('post')).order_by('-num_posts')[:10]

    context = {
        'form': form,
        'posts': posts_page,
        'suggested_users': suggested_users,
        'popular_hashtags': popular_hashtags,
    }
    return render(request, 'home.html', context)


def hashtag_posts_view(request, hashtag_name):
    hashtag = get_object_or_404(Hashtag, name=hashtag_name)
    all_posts = hashtag.post_set.all().select_related('author').annotate(comment_count=Count('comments')).order_by('-created_at')

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)

    if request.htmx:
        posts_page = _get_posts_with_interactions(request, posts_page)
        return render(request, 'posts/partials/post_list.html', {'posts': posts_page})

    posts_page = _get_posts_with_interactions(request, posts_page)

    context = {
        'hashtag': hashtag,
        'posts': posts_page,
    }
    return render(request, 'posts/hashtag_posts.html', context)


def search_view(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'posts')

    if request.htmx:
        if search_type == 'posts':
            found_posts = Post.objects.filter(content__icontains=query).select_related('author').annotate(comment_count=Count('comments')).order_by('-created_at') if query else Post.objects.none()
            paginator = Paginator(found_posts, 10)
            page_number = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_number)
            posts_page = _get_posts_with_interactions(request, posts_page)
            return render(request, 'posts/partials/post_list.html', {'posts': posts_page, 'query': query})
        
        elif search_type == 'users':
            found_users = User.objects.filter(username__icontains=query) if query else User.objects.none()
            paginator = Paginator(found_users, 15)
            page_number = request.GET.get('page', 1)
            users_page = paginator.get_page(page_number)
            return render(request, 'posts/partials/user_list.html', {'users': users_page, 'query': query})

    context = { 'query': query }
    return render(request, 'posts/search_results.html', context)


def post_detail_view(request, post_id):
    post = get_object_or_404(Post.objects.annotate(comment_count=Count('comments')), id=post_id)
    all_comments = post.comments.all().select_related('author')
    paginator = Paginator(all_comments, 10)
    page_number = request.GET.get('page', 1)
    comments_page = paginator.get_page(page_number)

    if request.htmx:
        if request.user.is_authenticated:
            comment_interactions = CommentInteraction.objects.filter(user=request.user, comment__in=comments_page).values('comment_id', 'interaction_type')
            comment_interactions_map = {item['comment_id']: item['interaction_type'] for item in comment_interactions}
            for comment in comments_page:
                comment.user_interaction = comment_interactions_map.get(comment.id)
                comment.absolute_url = request.build_absolute_uri(comment.get_absolute_url())
        return render(request, 'posts/partials/comment_list.html', {'comments': comments_page})

    comment_form = CommentForm()
    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            comment_cost = len(content)
            wallet = request.user.wallet
            if comment_cost > wallet.balance:
                messages.error(request, "Yanıt göndermek için yeterli harfiniz yok.")
            else:
                wallet.balance -= comment_cost
                wallet.save()
                new_comment = comment_form.save(commit=False)
                new_comment.post = post
                new_comment.author = request.user
                new_comment.save()
                messages.success(request, "Yanıtın başarıyla eklendi.")
            return redirect('posts:detail', post_id=post.id)

    if request.user.is_authenticated:
        post.user_interaction = post.get_user_interaction(request.user)
        comment_interactions = CommentInteraction.objects.filter(user=request.user, comment__in=comments_page).values('comment_id', 'interaction_type')
        comment_interactions_map = {item['comment_id']: item['interaction_type'] for item in comment_interactions}
        for comment in comments_page:
            comment.user_interaction = comment_interactions_map.get(comment.id)
            comment.absolute_url = request.build_absolute_uri(comment.get_absolute_url())

    post.absolute_url = request.build_absolute_uri(post.get_absolute_url())
    context = {
        'post': post,
        'comments': comments_page,
        'comment_form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)

# ... (interact_post, post_delete_view, comment_detail_view, interact_comment_view, comment_delete_view fonksiyonları aynı) ...


@login_required
def interact_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    post = get_object_or_404(Post, id=post_id)
    interaction_type = request.POST.get('interaction_type')

    if interaction_type not in ['L', 'D']:
        return JsonResponse({'error': 'Invalid interaction type'}, status=400)

    if post.author == request.user:
        return JsonResponse({'error': 'Cannot interact with your own post'}, status=403)

    existing_interaction = Interaction.objects.filter(user=request.user, post=post).first()
    post_author_wallet = post.author.wallet

    if existing_interaction:
        if existing_interaction.interaction_type == interaction_type:
            if interaction_type == 'L': post_author_wallet.balance -= 50
            else: post_author_wallet.balance += 1
            existing_interaction.delete()
        else:
            if existing_interaction.interaction_type == 'L': post_author_wallet.balance -= 50
            else: post_author_wallet.balance += 1
            if interaction_type == 'L': post_author_wallet.balance += 50
            else: post_author_wallet.balance -= 1
            existing_interaction.interaction_type = interaction_type
            existing_interaction.save()
    else:
        Interaction.objects.create(user=request.user, post=post, interaction_type=interaction_type)
        if interaction_type == 'L': post_author_wallet.balance += 50
        else: post_author_wallet.balance -= 1
    
    post_author_wallet.save()

    data = {
        'success': True,
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
    }
    return JsonResponse(data)


def post_detail_view(request, post_id):
    post = get_object_or_404(
        Post.objects.annotate(comment_count=Count('comments')), 
        id=post_id
    )
    
    all_comments = post.comments.all().select_related('author')
    paginator = Paginator(all_comments, 10)
    page_number = request.GET.get('page', 1)
    comments_page = paginator.get_page(page_number)

    if request.htmx:
        if request.user.is_authenticated:
            comment_interactions = CommentInteraction.objects.filter(user=request.user, comment__in=comments_page).values('comment_id', 'interaction_type')
            comment_interactions_map = {item['comment_id']: item['interaction_type'] for item in comment_interactions}
            for comment in comments_page:
                comment.user_interaction = comment_interactions_map.get(comment.id)
                comment.absolute_url = request.build_absolute_uri(comment.get_absolute_url())
        return render(request, 'posts/partials/comment_list.html', {'comments': comments_page})

    comment_form = CommentForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            comment_cost = len(content)
            wallet = request.user.wallet

            if comment_cost > wallet.balance:
                messages.error(request, "Yanıt göndermek için yeterli harfiniz yok.")
            else:
                wallet.balance -= comment_cost
                wallet.save()
                
                new_comment = comment_form.save(commit=False)
                new_comment.post = post
                new_comment.author = request.user
                new_comment.save()
                
                messages.success(request, "Yanıtın başarıyla eklendi.")
            
            return redirect('posts:detail', post_id=post.id)

    if request.user.is_authenticated:
        post.user_interaction = post.get_user_interaction(request.user)
        
        comment_interactions = CommentInteraction.objects.filter(user=request.user, comment__in=comments_page).values('comment_id', 'interaction_type')
        comment_interactions_map = {item['comment_id']: item['interaction_type'] for item in comment_interactions}
        for comment in comments_page:
            comment.user_interaction = comment_interactions_map.get(comment.id)
            comment.absolute_url = request.build_absolute_uri(comment.get_absolute_url())

    post.absolute_url = request.build_absolute_uri(post.get_absolute_url())

    context = {
        'post': post,
        'comments': comments_page,
        'comment_form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)

@login_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        return HttpResponseForbidden("Bu işlemi yapmaya yetkiniz yok.")

    if request.method == 'POST':
        try:
            post_cost = len(post.content)
            user_wallet = request.user.wallet
            user_wallet.balance += post_cost
            user_wallet.save()
            
            post.delete()
            
            messages.success(request, f"Bakla silindi ve {post_cost} harf iade edildi.")
        except Wallet.DoesNotExist:
            post.delete()
            messages.success(request, "Bakla başarıyla silindi.")
        
        return redirect('home')
    
    return redirect('posts:detail', post_id=post.id)


def hashtag_posts_view(request, hashtag_name):
    hashtag = get_object_or_404(Hashtag, name=hashtag_name)
    
    all_posts = hashtag.post_set.all().annotate(
        comment_count=Count('comments')
    ).order_by('-created_at')

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)

    if request.htmx:
        if request.user.is_authenticated:
            user_interactions = Interaction.objects.filter(user=request.user, post__in=posts_page).values('post_id', 'interaction_type')
            interactions_map = {item['post_id']: item['interaction_type'] for item in user_interactions}
            for post in posts_page:
                post.user_interaction = interactions_map.get(post.id)
                post.absolute_url = request.build_absolute_uri(post.get_absolute_url())
        return render(request, 'posts/partials/post_list.html', {'posts': posts_page})

    if request.user.is_authenticated:
        user_interactions = Interaction.objects.filter(user=request.user, post__in=posts_page).values('post_id', 'interaction_type')
        interactions_map = {item['post_id']: item['interaction_type'] for item in user_interactions}
        for post in posts_page:
            post.user_interaction = interactions_map.get(post.id)
            post.absolute_url = request.build_absolute_uri(post.get_absolute_url())

    context = {
        'hashtag': hashtag,
        'posts': posts_page,
    }
    return render(request, 'posts/hashtag_posts.html', context)



def comment_detail_view(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related('author', 'post', 'post__author'), id=comment_id)
    
    if request.user.is_authenticated:
        comment.user_interaction = comment.get_user_interaction(request.user)
        comment.post.user_interaction = comment.post.get_user_interaction(request.user)

    comment.absolute_url = request.build_absolute_uri(comment.get_absolute_url())
    comment.post.absolute_url = request.build_absolute_uri(comment.post.get_absolute_url())

    context = {'comment': comment}
    return render(request, 'posts/comment_detail.html', context)

@login_required
def interact_comment_view(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    comment = get_object_or_404(Comment, id=comment_id)
    interaction_type = request.POST.get('interaction_type')

    if interaction_type not in ['L', 'D']:
        return JsonResponse({'error': 'Invalid interaction type'}, status=400)

    if comment.author == request.user:
        return JsonResponse({'error': 'Cannot interact with your own comment'}, status=403)

    existing_interaction = CommentInteraction.objects.filter(user=request.user, comment=comment).first()
    comment_author_wallet = comment.author.wallet

    if existing_interaction:
        if existing_interaction.interaction_type == interaction_type:
            if interaction_type == 'L': comment_author_wallet.balance -= 50
            else: comment_author_wallet.balance += 1
            existing_interaction.delete()
        else:
            if existing_interaction.interaction_type == 'L': comment_author_wallet.balance -= 50
            else: comment_author_wallet.balance += 1
            if interaction_type == 'L': comment_author_wallet.balance += 50
            else: comment_author_wallet.balance -= 1
            existing_interaction.interaction_type = interaction_type
            existing_interaction.save()
    else:
        CommentInteraction.objects.create(user=request.user, comment=comment, interaction_type=interaction_type)
        if interaction_type == 'L': comment_author_wallet.balance += 50
        else: comment_author_wallet.balance -= 1
    
    comment_author_wallet.save()

    data = {
        'success': True,
        'like_count': comment.like_count,
        'dislike_count': comment.dislike_count,
    }
    return JsonResponse(data)

@login_required
def comment_delete_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return HttpResponseForbidden("Bu işlemi yapmaya yetkiniz yok.")
    if request.method == 'POST':
        post_id = comment.post.id
        try:
            comment_cost = len(comment.content)
            user_wallet = request.user.wallet
            user_wallet.balance += comment_cost
            user_wallet.save()
            messages.success(request, f"Yanıtın silindi ve {comment_cost} harf iade edildi.")
        except Wallet.DoesNotExist:
            messages.success(request, "Yanıtın silindi.")
        
        comment.delete()
        return redirect('posts:detail', post_id=post_id)
    return redirect('comments:detail', comment_id=comment.id)

# ... (diğer importlar) ...

def search_view(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'posts')

    # HTMX'ten bir istek gelirse, sayfalama yap ve ilgili parça şablonu gönder
    if request.htmx:
        if search_type == 'posts':
            found_posts = Post.objects.filter(content__icontains=query).select_related('author').annotate(comment_count=Count('comments')).order_by('-created_at') if query else Post.objects.none()
            paginator = Paginator(found_posts, 10)
            page_number = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_number)
            
            if request.user.is_authenticated:
                user_interactions = Interaction.objects.filter(user=request.user, post__in=posts_page).values('post_id', 'interaction_type')
                interactions_map = {item['post_id']: item['interaction_type'] for item in user_interactions}
                for post in posts_page:
                    post.user_interaction = interactions_map.get(post.id)
                    post.absolute_url = request.build_absolute_uri(post.get_absolute_url())
            
            return render(request, 'posts/partials/post_list.html', {'posts': posts_page, 'query': query})
        
        elif search_type == 'users':
            found_users = User.objects.filter(username__icontains=query) if query else User.objects.none()
            paginator = Paginator(found_users, 15)
            page_number = request.GET.get('page', 1)
            users_page = paginator.get_page(page_number)
            return render(request, 'posts/partials/user_list.html', {'users': users_page, 'query': query})

    # Normal, tam sayfa yüklemesi için SADECE iskeleti ve arama terimini gönder
    context = { 'query': query }
    return render(request, 'posts/search_results.html', context)
