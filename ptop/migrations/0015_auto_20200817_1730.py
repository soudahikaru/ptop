# Generated by Django 3.0.3 on 2020-08-17 08:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0014_auto_20200817_1728'),
    ]

    operations = [
        migrations.RenameField(
            model_name='troubleevent',
            old_name='device',
            new_name='device_id',
        ),
    ]
