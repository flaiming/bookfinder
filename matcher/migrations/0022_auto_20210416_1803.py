# Generated by Django 3.1.6 on 2021-04-16 18:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('matcher', '0021_auto_20210416_1754'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bookimport',
            old_name='auth_name',
            new_name='auth_user',
        ),
    ]