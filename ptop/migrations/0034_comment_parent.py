# Generated by Django 3.2.6 on 2021-10-13 08:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0033_auto_20211012_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ptop.comment', verbose_name='親コメント'),
        ),
    ]
