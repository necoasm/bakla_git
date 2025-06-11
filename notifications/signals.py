from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from posts.models import Post, Comment, Interaction, CommentInteraction
from users.models import User
from .models import Notification

# --- Beğeni / Beğenmeme Sinyalleri ---

@receiver(post_save, sender=Interaction)
def create_post_interaction_notification(sender, instance, created, **kwargs):
    if created:
        if instance.user != instance.post.author:
            if instance.interaction_type == 'L':
                verb = Notification.NotificationType.POST_LIKE
            else:
                verb = Notification.NotificationType.POST_DISLIKE
            
            Notification.objects.create(
                recipient=instance.post.author,
                sender=instance.user,
                verb=verb,
                action_object=instance.post
            )

@receiver(post_save, sender=CommentInteraction)
def create_comment_interaction_notification(sender, instance, created, **kwargs):
    if created:
        if instance.user != instance.comment.author:
            if instance.interaction_type == 'L':
                verb = Notification.NotificationType.COMMENT_LIKE
            else:
                verb = Notification.NotificationType.COMMENT_DISLIKE

            Notification.objects.create(
                recipient=instance.comment.author,
                sender=instance.user,
                verb=verb,
                action_object=instance.comment
            )

# TAKİP SİNYALİ BURADAN KALDIRILDI. BU İŞLEM ARTIK users/views.py İÇİNDE YAPILIYOR.

# --- Bahsetme Sinyalleri ---

@receiver(m2m_changed, sender=Post.mentions.through)
def create_post_mention_notification(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        sender_user = instance.author
        for user_id in pk_set:
            mentioned_user = User.objects.get(id=user_id)
            if sender_user != mentioned_user:
                Notification.objects.create(
                    recipient=mentioned_user,
                    sender=sender_user,
                    verb=Notification.NotificationType.MENTION,
                    action_object=instance
                )

@receiver(m2m_changed, sender=Comment.mentions.through)
def create_comment_mention_notification(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        sender_user = instance.author
        for user_id in pk_set:
            mentioned_user = User.objects.get(id=user_id)
            if sender_user != mentioned_user:
                Notification.objects.create(
                    recipient=mentioned_user,
                    sender=sender_user,
                    verb=Notification.NotificationType.MENTION,
                    action_object=instance
                )