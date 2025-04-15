from django.db import models
from base.model import BaseModel
from konkurs.models import Participant, Competition
from authentication.models import User


class Assessment(BaseModel):
    jury = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, blank=True, null=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.PositiveIntegerField(default=0)
    comment = models.TextField()

    def __str__(self):
        return f"{self.participant}"

