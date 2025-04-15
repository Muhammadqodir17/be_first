from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Winner, Notification


@receiver(post_save, sender=Winner)
def post_save_for_winner(sender, instance, created, **kwargs):
    message = (
        f'Congratulations {instance.participant.child.first_name}!. '
        f'You are the Winner of the {instance.competition.name} Competition'
    )
    Notification.objects.create(competition=instance.competition, message=message)