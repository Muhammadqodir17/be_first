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

RESULT_IMAGE = (
    (0, '---'),
    (1, 'Participants'),
    (2, 'Winners'),
    (3, 'Awards'),
    (4, 'Creative Works'),
)



class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=True, null=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.IntegerField(default=0)
    comment = models.TextField(blank=True)
    message = models.TextField(blank=True)
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

#dynamic
class ResultImage(BaseModel):
    name = models.IntegerField(choices=RESULT_IMAGE, default=0)
    image = models.ImageField(upload_to='media/', null=True)

    def __str__(self):
        return self.get_name_display()


class Policy(BaseModel):
    description = models.TextField()

    def __str__(self):
        return self.id


class AboutUs(BaseModel):
    title = models.CharField(max_length=300)
    sub_title = models.CharField(max_length=300)
    description = models.TextField()
    founder_name = models.CharField(max_length=100)
    founder_position = models.CharField(max_length=100)
    founder_image = models.ImageField(upload_to='media/')
    co_founder_name = models.CharField(max_length=100)
    co_founder_position = models.CharField(max_length=100)
    co_founder_image = models.ImageField(upload_to='media/')

    def __str__(self):
        return f'{self.title}'


class AboutResult(BaseModel):
    description = models.TextField()
    image = models.ImageField(upload_to='media/')

    def __str__(self):
        return f'{self.description}'


class ContactInformation(BaseModel):
    location = models.CharField(max_length=300)
    phone_number = models.CharField(max_length=13, unique=True)
    email = models.EmailField(unique=True)
    image = models.ImageField(upload_to='media/')

    def __str__(self):
        return f"{self.location}"


class SocialMedia(BaseModel):
    name = models.CharField(max_length=250)
    link = models.URLField()

    def __str__(self):
        return f'{self.link}'


class WebCertificate(BaseModel):
    data = models.DateField()
    image = models.ImageField(upload_to='media/', null=True)

    def __str__(self):
        return f'{self.data.year}' if self.data else "No Date"




