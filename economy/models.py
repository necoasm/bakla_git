# economy/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    # Bakiyenin eksiye düşebilmesi için IntegerField kullanıyoruz.
    balance = models.IntegerField(default=2500)

    def __str__(self):
        return f"{self.user.username}'s Wallet ({self.balance} harf)"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)