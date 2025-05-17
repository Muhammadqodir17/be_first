from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from konkurs_admin.models import Notification
from authentication.models import User
from konkurs.models import (
    Competition,
    Participant
)
from django.utils.translation import gettext as _


@receiver(post_save, sender=Competition)
def post_save_for_winner(sender, instance, created, **kwargs):
    if instance.status == 2:
        message = (
                _("%(name)s competition is finished. You can see your result") % {"name": instance.name}
        )
        participants = Participant.objects.filter(competition=instance)
        notifications = [
            Notification(user=participant.child.user, child=participant.child,
                         message=message, competition=participant.competition)
            for participant in participants if participant.child and participant.child.user
        ]
        with transaction.atomic():
            Notification.objects.bulk_create(notifications)

    if instance.status == 1:
        message = (
                _('%(name)s competition is started.') % {'name': instance.name}
        )
        participants = User.objects.filter(role=1)
        notifications = [
            Notification(user=participant,
                         message=message, competition=instance)
            for participant in participants
        ]
        with transaction.atomic():
            Notification.objects.bulk_create(notifications)
