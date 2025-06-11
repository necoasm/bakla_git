# posts/forms.py
from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-purple-500 focus:border-purple-500',
                'rows': 4,
                'placeholder': 'Ağzındaki baklayı çıkar...',
                'maxlength': '2500' # Tarayıcı tarafında karakter limitini uygula
            })
        }
        labels = {
            'content': ''
        }
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-purple-500 focus:border-purple-500',
                'rows': 2,
                'placeholder': 'Yanıtını buraya yaz...'
            })
        }
        labels = {
            'content': ''
        }
        