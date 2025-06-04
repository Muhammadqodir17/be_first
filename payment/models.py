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
