# Generated by Django 3.0.3 on 2020-08-17 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0011_auto_20200817_1719'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='troubleevent',
            name='device',
        ),
        migrations.AddField(
            model_name='troubleevent',
            name='device_id',
            field=models.TextField(max_length=100, null=True, verbose_name='device id'),
        ),
    ]
