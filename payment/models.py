from django.db import models
from base.model import BaseModel
from authentication.models import User


PAYMENT_METHOD = (
    (0, '---'),
    (1, 'CLICK'),
    (2, 'PAYME'),
)


class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    total_cost = models.IntegerField(default=0)
    payment_method = models.IntegerField(choices=PAYMENT_METHOD, default=0)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}'
