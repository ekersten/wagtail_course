from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    InlinePanel
)
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.core.fields import RichTextField
from modelcluster.fields import ParentalKey

from wagtailcaptcha.models import WagtailCaptchaEmailForm

# Create your models here.


class FormField(AbstractFormField):
    page = ParentalKey(
        'ContactPage',
        on_delete=models.CASCADE,
        related_name='form_fields'
    )

class ContactPage(WagtailCaptchaEmailForm):
    template = 'contact/contact_page.html'

    parent_page_types = ['home.HomePage']

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label='Form Fields'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname='col6'),
                FieldPanel('to_address', classname='col6')
            ]),
            FieldPanel('subject'),
        ], heading='Email Settings')
    ]
