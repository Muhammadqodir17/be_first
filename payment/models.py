from django.db import models
from authentication.models import User
from konkurs.models import Competition, Participant


class PurchaseModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='purchases')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='purchases')
    price = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}"

# class TransactionModel(models.Model):
#     transaction_id = models.CharField(max_length=100, verbose_name=_("Transaction ID"))
#     purchase = models.ForeignKey(PurchaseModel, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("Purchase"))
#     price = models.FloatField(verbose_name=_("Price"))
#     confirmed = models.BooleanField(default=False, verbose_name=_("Confirmed"))
#     confirm_time = models.DateTimeField(null=True, blank=True, verbose_name=_("Confirmed at"))
#     customer_card_token = models.CharField(max_length=255, null=True, verbose_name=_("Customer card token"))
#
#     class Meta:
#         verbose_name = "Transaction"
#         verbose_name_plural = "Transactions"
#         db_table = "transactions"
#
#     def __str__(self):
#         return f"{self.transaction_id} - {self.purchase}"
