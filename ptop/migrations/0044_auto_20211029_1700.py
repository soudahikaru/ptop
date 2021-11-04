# Generated by Django 3.2.6 on 2021-10-29 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0043_alter_supplyitem_remain_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplytype',
            name='level_name',
            field=models.CharField(default='', max_length=100, verbose_name='寿命指標の名称'),
        ),
        migrations.AlterField(
            model_name='supplytype',
            name='level_unit',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='寿命指標の単位'),
        ),
    ]
