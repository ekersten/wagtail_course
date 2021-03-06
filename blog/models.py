from django.db import models
from django.shortcuts import render
from django import forms
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.cache.utils import make_template_fragment_key
from django.core.cache import cache

from wagtail.api import APIField
from wagtail.core.models import Page, Orderable
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet
from wagtail.images.api.fields import ImageRenditionField

from taggit.models import TaggedItemBase

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager

from streams import blocks

from rest_framework.fields import Field

class ImageSerializedField(Field):
    def to_representation(self, value):
        return {
            'url': value.file.url,
            'title': value.title,
            'width': value.width,
            'height': value.height
        }

# Create your models here.

class BlogAuthorsOrderable(Orderable):
    page = ParentalKey('blog.BlogDetailPage', related_name='blog_authors')
    author = models.ForeignKey(
        'blog.BlogAuthor',
        on_delete=models.CASCADE
    )

    panels = [
        SnippetChooserPanel('author'),
    ]

    @property
    def author_name(self):
        return self.author.name

    @property
    def author_website(self):
        return self.author.website

    @property
    def author_image(self):
        return self.author.image

    api_fields = [
        APIField('author_name'),
        APIField('author_website'),
        # APIField('author_image', serializer=ImageSerializedField()),
        APIField(
            'image',
            serializer=ImageRenditionField(
                'fill-200x250',
                source='author_image'
            )
        ),
    ]


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

    api_fields = [
        APIField('name'),
        APIField('image'),
        APIField('website'),
    ]

    def __str__(self):
        return self.name

    class Meta: # noqa
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

register_snippet(BlogAuthor)


class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(
        verbose_name='slug',
        allow_unicode=True,
        max_length=255,
        help_text='Category Slug'
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('slug')
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']

register_snippet(BlogCategory)
class BlogListingPage(RoutablePageMixin, Page):

    template = 'blog/blog_listing_page.html'
    ajax_template = 'blog/blog_listing_page_ajax.html'
    max_count = 1
    subpage_types = ['blog.VideoBlogPage', 'blog.ArticleBlogPage']

    custom_title = models.CharField(max_length=100, blank=False, null=False, help_text='Overwrite default title')

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        all_posts  = BlogDetailPage.objects.live().public().order_by('-first_published_at')
        
        if request.GET.get('tag', None):
            tags = request.GET.get('tag')
            all_posts = all_posts.filter(tags__slug__in=[tags])

        if request.GET.get('category', None):
            category = request.GET.get('category')
            all_posts = all_posts.filter(categories__slug=category)

        paginator = Paginator(all_posts, 4)

        page =  request.GET.get('page')

        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        context['posts'] = posts

        # if request.GET.get('category') is not None:
        #     context['posts'] = context['posts'].filter(
        #         categories__slug=request.GET.get('category'))

        context['categories'] = BlogCategory.objects.all()
        return context

    @route(r'^latest/$', name='latest_posts')
    def latest_blog_posts_only_shows_last_5(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        context['latest_posts'] = BlogDetailPage.objects.live().public()[:3]
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

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogDetailPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )



class BlogDetailPage(Page):

    subpage_types = []
    parent_page_types = ['blog.BlogListingPage']

    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    custom_title = models.CharField(
        max_length=100, blank=False, null=False, help_text='Overwrite default title')

    banner_image = models.ForeignKey('wagtailimages.Image', blank=False, null=True, related_name='+', on_delete=models.SET_NULL)

    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)

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
        FieldPanel('tags'),
        ImageChooserPanel('banner_image'),
        MultiFieldPanel(
            [
                InlinePanel('blog_authors', label='Author', min_num=1, max_num=4)
            ],
            heading='Author(s)'
        ),
        MultiFieldPanel(
            [
                FieldPanel('categories', widget=forms.CheckboxSelectMultiple)
            ],
            heading='Categories'
        ),
        StreamFieldPanel('content'),
    ]

    api_fields = [
        APIField('blog_authors'),
        APIField('content'),
    ]

    def save(self, *args, **kwargs):
        key = make_template_fragment_key('blog_post_preview', [self.id])
        cache.delete(key)
        return super().save(*args, **kwargs)

# blog subclasses

class ArticleBlogPage(BlogDetailPage):
    template = 'blog/article_blog_page.html'
    
    subtitle = models.CharField(max_length=100, blank=True, null=True)
    intro_image = models.ForeignKey(
        'wagtailimages.Image',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='Best size: 1400x400'
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        FieldPanel('subtitle'),
        FieldPanel('tags'),
        ImageChooserPanel('banner_image'),
        ImageChooserPanel('intro_image'),
        MultiFieldPanel(
            [
                InlinePanel('blog_authors', label='Author',
                            min_num=1, max_num=4)
            ],
            heading='Author(s)'
        ),
        MultiFieldPanel(
            [
                FieldPanel('categories', widget=forms.CheckboxSelectMultiple)
            ],
            heading='Categories'
        ),
        StreamFieldPanel('content'),
    ]


class VideoBlogPage(BlogDetailPage):
    template = 'blog/video_blog_page.html'

    youtube_video_id = models.CharField(max_length=30)

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        ImageChooserPanel('banner_image'),
        MultiFieldPanel(
            [
                InlinePanel('blog_authors', label='Author',
                            min_num=1, max_num=4)
            ],
            heading='Author(s)'
        ),
        MultiFieldPanel(
            [
                FieldPanel('categories', widget=forms.CheckboxSelectMultiple)
            ],
            heading='Categories'
        ),
        FieldPanel('youtube_video_id'),
        StreamFieldPanel('content'),
    ]
