from django.db import models
from base.model import BaseModel
from child.models import Child


STATUS = (
    (0, '---'),
    (1, 'Active'),
    (2, 'Finished')
)

APPROVEMENT = (
    (1, '---'),
    (2, 'Accepted'),
    (3, 'Rejected'),
)

MARKED_STATUS = (
    (1, 'Not Marked'),
    (2, 'Marked')
)


class Category(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name}'


class Competition(BaseModel):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    prize = models.TextField()
    comp_start_date = models.DateField()
    comp_start_time = models.TimeField()
    comp_end_date = models.DateField()
    comp_end_time = models.TimeField()
    application_start_date = models.DateField()
    application_start_time = models.TimeField()
    application_end_date = models.DateField()
    application_end_time = models.TimeField()
    participation_fee = models.FloatField(default=0)
    rules = models.TextField()
    physical_certificate = models.ImageField(upload_to='media/', blank=True)
    image = models.ImageField(upload_to='media/', blank=True)
    status = models.IntegerField(choices=STATUS, default=1)

    def __str__(self):
        return f'{self.name}'


class GradeCriteria(BaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    criteria = models.CharField(max_length=250)

    def __str__(self):
        return f'{self.criteria}'


class Participant(BaseModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=True, null=True, related_name='child')
    physical_certificate = models.BooleanField(default=False)
    action = models.IntegerField(choices=APPROVEMENT, default=1)
    marked_status = models.IntegerField(choices=MARKED_STATUS, default=1)
    winner = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.child}"


class ChildWork(BaseModel):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, blank=True, null=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=True, null=True)
    files = models.FileField(upload_to='media/', blank=True)

    def __str__(self):
        return f"{self.participant}"


class ContactUs(BaseModel):
    email = models.EmailField(unique=True)
    replied = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.email}'
