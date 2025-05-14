from django.contrib import admin
from .models import (
    User,
    SMSCode,
    TemporaryPassword,
    OTPRegisterResend,
    OTPSetPassword
)

admin.site.register(User)
admin.site.register(SMSCode)
admin.site.register(TemporaryPassword)
admin.site.register(OTPRegisterResend)
admin.site.register(OTPSetPassword)
