# Generated by Django 3.2.9 on 2021-12-10 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dynamic', '0011_synctask_fail_msg'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimelineEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.JSONField()),
                ('event_time', models.DateTimeField()),
                ('type', models.CharField(choices=[('UN', 'Unknown'), ('ST', 'Stream'), ('LO', 'Lottery'), ('RE', 'Release')], default='NT', max_length=2)),
                ('dynamic', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='dynamic.dynamic')),
            ],
        ),
    ]
