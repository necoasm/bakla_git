from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        POST_LIKE = 'PL', 'Post Like'
        POST_DISLIKE = 'PD', 'Post Dislike' # Beğenmeme için yeni tür
        COMMENT_LIKE = 'CL', 'Comment Like'
        COMMENT_DISLIKE = 'CD', 'Comment Dislike' # Beğenmeme için yeni tür
        FOLLOW = 'F', 'Follow'
        MENTION = 'M', 'Mention'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    verb = models.CharField(max_length=2, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    action_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} -> {self.recipient}: {self.get_verb_display()}'