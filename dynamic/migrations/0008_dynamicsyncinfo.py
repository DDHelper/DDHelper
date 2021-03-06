# Generated by Django 3.2.9 on 2021-12-03 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0007_rename_member_dynamicmember'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicSyncInfo',
            fields=[
                ('sid', models.BigAutoField(primary_key=True, serialize=False)),
                ('sync_start_time', models.DateTimeField(auto_now_add=True)),
                ('sync_update_time', models.DateTimeField(auto_now=True)),
                ('total_tasks', models.IntegerField()),
                ('success_tasks', models.IntegerField()),
                ('failed_tasks', models.IntegerField()),
            ],
        ),
    ]
