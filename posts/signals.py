from django.db.models.signals import post_save
from django.dispatch import receiver
import re
from .models import Post, Comment, Hashtag
from users.models import User

def process_content(instance, content_field_name):
    """
    Hem Post hem de Comment için ortak olan mention ve hashtag işleme mantığı.
    """
    # Hashtag'leri işle
    hashtag_names = re.findall(r'#(\w+)', getattr(instance, content_field_name))
    if hashtag_names:
        hashtag_objects = []
        for name in hashtag_names:
            hashtag, created = Hashtag.objects.get_or_create(name=name.lower())
            hashtag_objects.append(hashtag)
        instance.hashtags.set(hashtag_objects)
    else:
        instance.hashtags.clear()

    # Mention'ları işle
    mentioned_usernames = re.findall(r'@(\w+)', getattr(instance, content_field_name))
    if mentioned_usernames:
        mentioned_users = User.objects.filter(username__in=mentioned_usernames)
        instance.mentions.set(mentioned_users)
    else:
        instance.mentions.clear()

@receiver(post_save, sender=Post)
def process_post_content(sender, instance, created, **kwargs):
    """Bir Post kaydedildikten sonra içeriğini işle."""
    process_content(instance, 'content')

@receiver(post_save, sender=Comment)
def process_comment_content(sender, instance, created, **kwargs):
    """Bir Comment kaydedildikten sonra içeriğini işle."""
    # Comment modelinde hashtags alanı olmadığı için bu sinyal şimdilik sadece mention işler.
    # Eğer yorumlara da hashtag eklemek istersek, Comment modeline de hashtags alanı eklemeliyiz.
    mentioned_usernames = re.findall(r'@(\w+)', instance.content)
    if mentioned_usernames:
        mentioned_users = User.objects.filter(username__in=mentioned_usernames)
        instance.mentions.set(mentioned_users)
    else:
        instance.mentions.clear()