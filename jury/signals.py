from django.db.models.signals import post_save
from django.dispatch import receiver
from konkurs_admin.models import Notification
from .models import Assessment


@receiver(post_save, sender=Assessment)
def post_save_for_winner(sender, instance, created, **kwargs):
    message = (
        'Jury graded your work. You can see your feedbacks'
    )
    Notification.objects.create(
        user=instance.participant.child.user, child=instance.participant.child,
        grade=instance.grade, comment=instance.comment, message=message,
        competition=instance.participant.competition
    )