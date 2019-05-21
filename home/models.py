from django.db import models
from django.shortcuts import render

from modelcluster.fields import ParentalKey

from wagtail.api import APIField
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel, StreamFieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.fields import StreamField
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from streams import blocks


class HomePageCarouselImages(Orderable):
    page = ParentalKey('home.HomePage', related_name='carousel_images')
    carousel_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    panels = [
        ImageChooserPanel('carousel_image')
    ]

class HomePage(RoutablePageMixin, Page):
    banner_title = models.CharField(max_length=100, blank=False, null=True)
    banner_subtitle = RichTextField(features=['bold', 'italic'])
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_cta = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content = StreamField(
        [
            ('cta', blocks.CTABlock()),
        ],
        null=True,
        blank=True
    )
    
    # only one on site
    max_count = 1

    # search_fields = Page.search_fields + [
        
    # ]

    api_fields = [
        APIField('banner_title'),
        APIField('banner_subtitle'),
        APIField('banner_image'),
        APIField('banner_cta'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('banner_title'),
            FieldPanel('banner_subtitle'),
            ImageChooserPanel('banner_image'),
            PageChooserPanel('banner_cta'),
        ], heading='Banners Options'),
        MultiFieldPanel([
            InlinePanel('carousel_images', max_num=5, min_num=1,label='Image'),
        ], heading='Carousel Images'),
        StreamFieldPanel('content'),
    ]

    class Meta:
        verbose_name = 'Home Page'
        verbose_name_plural = 'Home Pages'

    @route(r'^subscribe/$')
    def the_subscribe_page(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        context['a_special_text'] = 'Hello world 123123'
        return render(request, 'home/subscribe.html', context)
