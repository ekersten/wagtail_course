# Generated by Django 2.2.1 on 2019-05-23 18:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('behance', '0004_behanceprojectmodule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='behanceproject',
            name='cover',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image'),
        ),
    ]
