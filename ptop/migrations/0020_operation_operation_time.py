# Generated by Django 3.0.3 on 2021-01-12 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0019_auto_20210112_1945'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='operation_time',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='運転時間'),
        ),
    ]
