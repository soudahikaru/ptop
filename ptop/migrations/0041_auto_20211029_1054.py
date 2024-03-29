# Generated by Django 3.2.8 on 2021-10-29 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0040_auto_20211029_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplytype',
            name='model_number',
            field=models.CharField(default='', max_length=100, verbose_name='型式番号'),
        ),
        migrations.AddField(
            model_name='supplytype',
            name='vendor_name',
            field=models.CharField(default='', max_length=100, verbose_name='メーカー名'),
        ),
        migrations.AlterField(
            model_name='supplytype',
            name='name',
            field=models.CharField(default='', max_length=100, verbose_name='名称'),
        ),
    ]
