# Generated by Django 3.1.6 on 2021-02-28 20:27

from django.db import migrations, models
import matcher.models


class Migration(migrations.Migration):

    dependencies = [
        ('matcher', '0004_auto_20210227_2042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookcover',
            name='image',
            field=models.ImageField(blank=True, upload_to=matcher.models.get_book_cover_image_path),
        ),
    ]
