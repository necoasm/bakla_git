from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    followers = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='following',
        blank=True
    )
    
    # --- YENİ ALANLAR ---
    # blank=True -> Bu alanın boş olmasına izin ver.
    # null=True -> Veritabanında bu alanın NULL olmasına izin ver.
    bio = models.TextField(max_length=160, blank=True, null=True)
    # upload_to='profile_pics/' -> Yüklenen dosyalar MEDIA_ROOT/profile_pics/ klasörüne kaydedilecek.
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # --- YENİ ALANLAR SONU ---

    def __str__(self):
        return self.username

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.following.count()