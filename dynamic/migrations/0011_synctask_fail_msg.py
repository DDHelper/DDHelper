# Generated by Django 3.2.9 on 2021-12-04 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0010_auto_20211204_1003'),
    ]

    operations = [
        migrations.AddField(
            model_name='synctask',
            name='fail_msg',
            field=models.TextField(null=True),
        ),
    ]
