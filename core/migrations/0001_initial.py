# Generated by Django 3.1.6 on 2021-05-08 19:00

import core.models
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
                ('other_names', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=list, size=None)),
                ('isbn', models.CharField(blank=True, max_length=20)),
                ('pages', models.PositiveIntegerField(default=0)),
                ('language', models.CharField(blank=True, max_length=20)),
                ('year', models.PositiveIntegerField(blank=True, null=True)),
                ('authors', models.ManyToManyField(related_name='books', to='core.Author')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='BookImport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=50)),
                ('url', models.TextField()),
                ('price_type', models.PositiveIntegerField(choices=[(1, 'Offer'), (2, 'Request'), (3, 'New'), (4, 'Used')])),
                ('active', models.BooleanField(default=True)),
                ('devider_in_name', models.CharField(blank=True, max_length=1)),
                ('auth_user', models.CharField(blank=True, max_length=20)),
                ('auth_password', models.CharField(blank=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='BookProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True)),
                ('url', models.URLField(max_length=255, unique=True)),
                ('books', models.ManyToManyField(related_name='profiles', to='core.Book')),
            ],
        ),
        migrations.CreateModel(
            name='BookPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('price', models.PositiveIntegerField()),
                ('orig_id', models.CharField(max_length=20)),
                ('price_type', models.PositiveIntegerField(choices=[(1, 'Offer'), (2, 'Request'), (3, 'New'), (4, 'Used')])),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='core.book')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='core.bookprofile')),
                ('source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='core.source')),
            ],
        ),
        migrations.CreateModel(
            name='BookCover',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('image', models.ImageField(blank=True, upload_to=core.models.get_book_cover_image_path)),
                ('image_url', models.URLField(max_length=255)),
                ('hash_short', models.CharField(blank=True, max_length=64)),
                ('hash_long', models.CharField(blank=True, max_length=256)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='covers', to='core.book')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='covers', to='core.bookprofile')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]