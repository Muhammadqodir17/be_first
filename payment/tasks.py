from celery import shared_task
from django.utils.timezone import now
from django_celery_beat.models import CrontabSchedule, PeriodicTask, ClockedSchedule
import json
from datetime import datetime, timedelta
from .utils import pay_create, pay_pre_apply, pay_apply
from django.utils.translation import gettext_lazy as _
import asyncio
from .models import PurchaseModel


@shared_task
def inactivate_purchase(purchase_id):
    try:
        purchase = PurchaseModel.objects.get(id=purchase_id)
        purchase.is_active = False
        purchase.save()
    except PurchaseModel.DoesNotExist:
        ...

@shared_task
def register_purchase_delay(purchase_id):
    try:
        purchase = PurchaseModel.objects.get(id=purchase_id)
        run_time = now() + timedelta(days=90)
        clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=run_time)
        task_name = f"inactivate-purchase-{purchase.id}"
        PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'payment.tasks.inactivate_purchase',
                'clocked': clocked,
                'one_off': True,
                'args': json.dumps([purchase.id]),
            }
        )
    except PurchaseModel.DoesNotExist:
        pass

def month_of_year(start: int):
    def next_month():
        nonlocal start
        while True:
            start += 3
            yield str(start)
    return next_month()


async def payment_process(user_id, card_token: str, amount: int, purchase_id: int):
    try:
        transaction_id = await pay_create(amount, purchase_id)
    except Exception:
        await send_exception(user_id, _("Failed to pay by schedule"))
        return False
    try:
        await pay_pre_apply(transaction_id, card_token)
    except Exception:
        await send_exception(user_id, _("Failed to pay by schedule"))
        return False
    try:
        await pay_apply(transaction_id, 111111)
    except Exception:
        await send_exception(user_id, _("Failed to pay by schedule"))
        return False
    return True

async def send_exception(user_id: int, exception: str):
    from config.bot import bot
    await bot.send_message(user_id, exception)

