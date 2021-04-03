# Generated by Django 3.1.6 on 2021-03-21 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matcher', '0015_book_authors'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='author',
        ),
        migrations.AlterField(
            model_name='book',
            name='authors',
            field=models.ManyToManyField(null=True, related_name='books', to='matcher.Author'),
        ),
    ]