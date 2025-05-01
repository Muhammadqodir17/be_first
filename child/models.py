from django.db import models
from django.contrib.auth import get_user_model
from base.model import BaseModel

User = get_user_model()

DEGREE_OF_KINSHIP_CHOICES = (
    ('son', 'Son'),
    ('daughter', 'Daughter'),
    ('nephew', 'Nephew'),
    ('niece', 'Niece'),
    ('grandchild', 'Grandchild'),
)


class Child(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    place_of_study = models.CharField(max_length=100)
    degree_of_kinship = models.CharField(choices=DEGREE_OF_KINSHIP_CHOICES, max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
