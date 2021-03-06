# Generated by Django 3.2.8 on 2021-11-11 12:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dynamic', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('group_name', models.CharField(max_length=100)),
                ('gid', models.BigIntegerField(primary_key=True, serialize=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SubscribeList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscribe.usergroup')),
                ('mem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dynamic.member')),
            ],
        ),
    ]
