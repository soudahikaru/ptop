# Generated by Django 3.0.3 on 2020-12-01 01:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0008_auto_20201130_1653'),
    ]

    operations = [
        migrations.AddField(
            model_name='troubleevent',
            name='operation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ptop.OperationType', verbose_name='発生時の運転内容'),
        ),
    ]
