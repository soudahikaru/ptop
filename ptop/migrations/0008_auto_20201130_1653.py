# Generated by Django 3.0.3 on 2020-11-30 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0007_operation_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='comment',
            field=models.TextField(blank=True, null=True, verbose_name='コメント'),
        ),
    ]
