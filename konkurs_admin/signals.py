from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Winner, Notification
from django.utils.translation import gettext as _


@receiver(post_save, sender=Winner)
def post_save_for_winner(sender, instance, created, **kwargs):
    message = (
        _('Congratulations %(name)s!.') % {'name': instance.participant.child.first_name},
        _('You are the Winner of the %(comp)s Competition') % {'comp': instance.participant.child.first_name}
    )
    Notification.objects.create(competition=instance.competition, message=message)