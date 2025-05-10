from django.contrib import admin
from .models import (
    Category,
    Competition,
    Participant,
    ChildWork,
    GradeCriteria,
    ContactUs,
)

admin.site.register(Category)
admin.site.register(Competition)
admin.site.register(Participant)
admin.site.register(ChildWork)
admin.site.register(GradeCriteria)
admin.site.register(ContactUs)
