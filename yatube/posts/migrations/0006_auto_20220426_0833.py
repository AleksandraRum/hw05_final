# Generated by Django 2.2.16 on 2022-04-26 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_follow'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='create',
            new_name='created',
        ),
    ]
