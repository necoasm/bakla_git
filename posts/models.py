from django.db import models
from django.conf import settings
from django.urls import reverse
from users.models import User

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_posts', blank=True)
    hashtags = models.ManyToManyField(Hashtag, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.content[:30]}'

    @property
    def like_count(self):
        return self.interactions.filter(interaction_type='L').count()

    @property
    def dislike_count(self):
        return self.interactions.filter(interaction_type='D').count()

    def get_user_interaction(self, user):
        if not user.is_authenticated:
            return None
        try:
            interaction = self.interactions.get(user=user)
            return interaction.interaction_type
        except Interaction.DoesNotExist:
            return None
            
    def get_absolute_url(self):
        return reverse('posts:detail', kwargs={'post_id': self.id})


class Interaction(models.Model):
    class InteractionType(models.TextChoices):
        LIKE = 'L', 'Like'
        DISLIKE = 'D', 'Dislike'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=1, choices=InteractionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')


class Comment(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_comments', blank=True)
    # Yorumlara da hashtag eklemek istersek, buraya bir ManyToManyField ekleyebiliriz.
    # hashtags = models.ManyToManyField(Hashtag, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post}'
    
    def get_absolute_url(self):
        return reverse('comments:detail', kwargs={'comment_id': self.id})

    @property
    def like_count(self):
        return self.comment_interactions.filter(interaction_type='L').count()

    @property
    def dislike_count(self):
        return self.comment_interactions.filter(interaction_type='D').count()
        
    def get_user_interaction(self, user):
        if not user.is_authenticated:
            return None
        try:
            interaction = self.comment_interactions.get(user=user)
            return interaction.interaction_type
        except CommentInteraction.DoesNotExist:
            return None

class CommentInteraction(models.Model):
    class InteractionType(models.TextChoices):
        LIKE = 'L', 'Like'
        DISLIKE = 'D', 'Dislike'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_interactions')
    interaction_type = models.CharField(max_length=1, choices=InteractionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')