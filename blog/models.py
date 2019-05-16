from django.db import models
from django.shortcuts import render

from wagtail.core.models import Page
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet

from streams import blocks

# Create your models here.

class BlogAuthor(models.Model):
    name = models.CharField(max_length=100, )
    website = models.URLField(blank=True, null=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='+'
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('name'),
                ImageChooserPanel('image'),

            ],
            heading = 'Name and Image'
        ),
        MultiFieldPanel(
            [
                FieldPanel('website')
            ],
            heading='Link'
        )
    ]

    def __str__(self):
        return self.name

    class Meta: # noqa
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

register_snippet(BlogAuthor)

class BlogListingPage(RoutablePageMixin, Page):

    template = 'blog/blog_listing_page.html'

    custom_title = models.CharField(max_length=100, blank=False, null=False, help_text='Overwrite default title')

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['posts'] = BlogDetailPage.objects.live().public()
        return context

    @route(r'^latest/$', name='latest_posts')
    def latest_blog_posts_only_shows_last_5(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        context['latest_posts'] = BlogDetailPage.objects.live().public()[:1]
        return render(request, 'blog/latest_posts.html', context)

    def get_sitemap_urls(self, request=None):
        # uncoment to have no sitemap for this page
        # return []
        sitemap = super().get_sitemap_urls(request=request)
        sitemap.append({
            'location': self.full_url + self.reverse_subpage('latest_posts'),
            'lastmod': (self.last_published_at or self.latest_revision_created_at),
            'priority': 0.9
        })
        return sitemap


class BlogDetailPage(Page):
    custom_title = models.CharField(
        max_length=100, blank=False, null=False, help_text='Overwrite default title')

    blog_image = models.ForeignKey('wagtailimages.Image', blank=False, null=True, related_name='+', on_delete=models.SET_NULL)

    content = StreamField(
        [
            ('title_and_text', blocks.TitleAndTextBlock()),
            ('full_richtext', blocks.RichTextBlock()),
            ('simple_richtext', blocks.SimpleRichTextBlock()),
            ('cards', blocks.CardBlock()),
            ('cta', blocks.CTABlock()),
        ],
        null=True,
        blank=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        ImageChooserPanel('blog_image'),
        StreamFieldPanel('content')
    ]
