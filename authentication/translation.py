from modeltranslation.translator import translator, TranslationOptions
from .models import User


class ExpertTranslationOptions(TranslationOptions):
    fields = ('speciality', 'place_of_work')


translator.register(User, ExpertTranslationOptions)