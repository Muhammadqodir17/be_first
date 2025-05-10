from django.contrib import admin
from .models import (
    Notification,
    Winner,
    ResultImage,
    Policy,
    AboutUs,
    AboutResult,
    ContactInformation,
    SocialMedia,
    WebCertificate,
)

admin.site.register(Notification)
admin.site.register(Winner)
admin.site.register(WebCertificate)
#dynamic
admin.site.register(ResultImage)
admin.site.register(Policy)
admin.site.register(AboutUs)
admin.site.register(AboutResult)
admin.site.register(ContactInformation)
admin.site.register(SocialMedia)
