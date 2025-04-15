from django.db import models
from base.model import BaseModel
from authentication.models import User
from child.models import Child
from konkurs.models import (
    Competition,
    Participant
)


PLACE = (
    (0, '---'),
    (1, 'First Place'),
    (2, 'Second Place'),
    (3, 'Third Place')
)


class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=True, null=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}'


class Winner(BaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    place = models.IntegerField(choices=PLACE, default=0)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='participant')
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    grade = models.IntegerField(default=0)
    jury_comment = models.TextField()
    certificate = models.FileField(upload_to='media/', blank=True)
    address_for_physical_certificate = models.TextField()

    def __str__(self):
        return f'{self.participant}'


