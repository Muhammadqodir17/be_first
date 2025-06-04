from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from konkurs_admin.models import Notification
from authentication.models import User
from konkurs.models import Competition
from django.utils.translation import gettext_lazy  as _


@shared_task(name='celery_tasks.tasks.send_notification_to_all_users')
def send_notification_to_all_users(competition, message):
    users = User.objects.filter(role=1)  # Get all users
    # users = SubscriptionModel.objects.filter(user__role=1)

    notifications = [
        Notification(user=sub.user, competition=competition, message=message)
        for sub in users
    ]

    Notification.objects.bulk_create(notifications)


@shared_task(name='celery_tasks.tasks.check_competition_notifications')
def check_competition_notifications():
    current_time = now()

    ### For register ###
    # 3 days before starting register
    app_start_in_3 = Competition.objects.filter(
        application_start_date=current_time.date() + timedelta(days=3),
        application_start_time__hour=current_time.hour,
        application_start_time__minute=current_time.minute
    )
    for app in app_start_in_3:
        send_notification_to_all_users.delay(
            app,
            _("Registration for %(name)s will start in 3 days!") % {'name': app.name}
        )

    # 🔹 Check if Registration Starts Now (Matching Date & Time)
    app_starting = Competition.objects.filter(
        application_start_date=current_time.date(),
        application_start_time__hour=current_time.hour,
        application_start_time__minute=current_time.minute
    )
    for app in app_starting:
        send_notification_to_all_users(
            app,
            _("Registration for %(app_name)s has started!") % {'app_name': app.name}
        )

    # # 🔹 Check if Registration Ends in 3 Days (Matching Date)
    app_end_in_3 = Competition.objects.filter(
        application_end_date=current_time.date() + timedelta(days=3),
        application_end_time__hour=current_time.hour,
        application_end_time__minute=current_time.minute
    )
    for app in app_end_in_3:
        send_notification_to_all_users(
            app,
            _("Registration for %(app_name)s ends in 3 days!") % {'app_name': app.name}
        )

    # # end register date
    app_end = Competition.objects.filter(
        application_end_date=current_time.date(),
        application_end_time__hour=current_time.hour,
        application_end_time__minute=current_time.minute
    )
    for app in app_end:
        send_notification_to_all_users(
            app,
            _("Registration for %(app_name)s ended. Good luck in Competition!") % {'app_name': app.name}
        )

    # ### For comp ###
    # 3 days before starting comp
    competition_start_in_3 = Competition.objects.filter(
        comp_start_date=current_time.date() + timedelta(days=3),
        comp_start_time__hour=current_time.hour,
        comp_start_time__minute=current_time.minute
    )
    for competition in competition_start_in_3:
        send_notification_to_all_users(
            competition,
            _("%(name)s competition will start in 3 days!") % {'name': competition.name}
        )

    # # 🔹 Check if Comp Starts Now (Matching Date & Time)
    # competitions_starting = Competition.objects.filter(
    #     comp_start_date=current_time.date(),
    #     comp_start_time__hour=current_time.hour,
    #     comp_start_time__minute=current_time.minute
    # )
    # for competition in competitions_starting:
    #     send_notification_to_all_users(
    #         competition,
    #         f"{competition.name} competition has started!. Look at it!"
    #     )

    # # 🔹 Check if Comp Ends in 3 Days (Matching Date)
    competitions_end_in_3 = Competition.objects.filter(
        comp_end_date=current_time.date() + timedelta(days=3),
        application_end_time__hour=current_time.hour,
        application_end_time__minute=current_time.minute
    )
    for competition in competitions_end_in_3:
        send_notification_to_all_users(
            competition,
            _("%(comp_name)s competition ends in 3 days!. HURRY!!!") % {'comp_name': competition.name}
        )

    # end comp date
    # competitions_ending = Competition.objects.filter(
    #     comp_end_date=current_time.date(),
    #     comp_end_time__hour=current_time.hour,
    #     comp_end_time__minute=current_time.minute
    # )
    # for competition in competitions_ending:
    #     send_notification_to_all_users(
    #         competition,
    #         f"{competition.name} competition ended. Good luck!"
    #     )