# Generated by Django 3.2.8 on 2021-10-21 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0036_troublecommunicationsheet'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_tcs_destination',
            field=models.BooleanField(default=False, help_text='不具合連絡票送信先に含める'),
        ),
    ]
