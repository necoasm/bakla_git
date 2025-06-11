from django import template
from django.urls import reverse
from django.utils.html import format_html
import re

register = template.Library()

@register.filter(name='linkify')
def linkify(text):
    # Önce hashtag'leri linke çevir
    def replace_hashtag(match):
        hashtag = match.group(1)
        url = reverse('posts:hashtag_posts', args=[hashtag.lower()])
        return format_html('<a href="{}" class="text-blue-600 font-semibold hover:underline">#{}</a>', url, hashtag)
    
    linked_text = re.sub(r'#(\w+)', replace_hashtag, str(text))

    # Sonra mention'ları linke çevir
    def replace_mention(match):
        username = match.group(1)
        try:
            profile_url = reverse('profile', args=[username])
            return format_html('<a href="{}" class="text-purple-600 font-semibold hover:underline">@{}</a>', profile_url, username)
        except:
            return match.group(0)
            
    return format_html(re.sub(r'@(\w+)', replace_mention, linked_text))