from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import PurchaseModel
from .tasks import register_purchase_delay

@receiver(post_save, sender=PurchaseModel)
def purchase_inactive_delay_register(sender, created, instance, *args, **kwargs):
    if created:
        register_purchase_delay.delay(instance.id)
