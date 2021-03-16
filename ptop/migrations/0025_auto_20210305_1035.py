# Generated by Django 3.0.3 on 2021-03-05 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0024_auto_20210304_2221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='troubleevent',
            name='handling_operators',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='対応者'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='input_operator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='troubleevent_inputed', to=settings.AUTH_USER_MODEL, verbose_name='入力者'),
        ),
    ]