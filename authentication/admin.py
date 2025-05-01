from django.contrib import admin
from .models import User, SMSCode, TemporaryPassword

admin.site.register(User)
admin.site.register(SMSCode)
admin.site.register(TemporaryPassword)
