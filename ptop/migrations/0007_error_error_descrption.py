# Generated by Django 3.0.3 on 2020-08-17 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0006_auto_20200817_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='error_descrption',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='エラー説明'),
        ),
    ]
