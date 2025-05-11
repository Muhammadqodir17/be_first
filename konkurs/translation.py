from modeltranslation.translator import translator, TranslationOptions
from .models import (
    Competition, Category,
)
from konkurs_admin.models import (
    ContactInformation,
    AboutResult,
    AboutUs,
    Policy,
)


class CategoryTranslationOptions(TranslationOptions):
    fields = ['name']


class CompetitionTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class ContactInformationTranslationOptions(TranslationOptions):
    fields = ['location']


class AboutResultTranslationOptions(TranslationOptions):
    fields = ['description']


class AboutUsTranslationOptions(TranslationOptions):
    fields = ('title', 'sub_title', 'description', 'founder_position', 'co_founder_position')


class PolicyTranslationOptions(TranslationOptions):
    fields = ['description']


translator.register(Competition, CompetitionTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(ContactInformation, ContactInformationTranslationOptions)
translator.register(AboutResult, AboutResultTranslationOptions)
translator.register(AboutUs, AboutUsTranslationOptions)
translator.register(Policy, PolicyTranslationOptions)
