# Generated by Django 3.0.3 on 2020-11-26 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0006_auto_20201126_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='comment',
            field=models.TextField(null=True, verbose_name='コメント'),
        ),
    ]
