# Generated by Django 3.2.9 on 2021-12-03 03:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0004_auto_20211201_1316'),
        ('dynamic', '0003_alter_member_mid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='face',
        ),
        migrations.RemoveField(
            model_name='member',
            name='name',
        ),
        migrations.AlterField(
            model_name='dynamic',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscribe.subscribemember'),
        ),
    ]
