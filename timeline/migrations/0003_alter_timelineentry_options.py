# Generated by Django 3.2.9 on 2021-12-23 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_auto_20211216_1237'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timelineentry',
            options={'ordering': ['-event_time']},
        ),
    ]
