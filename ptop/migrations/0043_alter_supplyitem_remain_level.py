# Generated by Django 3.2.6 on 2021-10-29 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0042_rename_type_supplyitem_supplytype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplyitem',
            name='remain_level',
            field=models.FloatField(blank=True, null=True, verbose_name='寿命指標'),
        ),
    ]
