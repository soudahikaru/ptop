# Generated by Django 3.0.3 on 2021-03-04 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0022_auto_20210304_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='troubleevent',
            name='downtime',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='装置故障時間'),
        ),
    ]
