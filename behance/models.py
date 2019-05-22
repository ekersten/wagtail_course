from django.db import models
from django_extensions.db.fields import AutoSlugField
from wagtailorderable.models import Orderable

# Create your models here.
class BehanceProject(Orderable, models.Model):
    behance_id = models.PositiveIntegerField()
    behance_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', overwrite=True)

    class Meta:
        verbose_name = 'Behance Project'
        verbose_name_plural = 'Behance Projects'
    
