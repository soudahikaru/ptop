# Generated by Django 3.0.3 on 2020-08-26 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0026_auto_20200824_2255'),
    ]

    operations = [
        migrations.AddField(
            model_name='troublegroup',
            name='classify_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='分類ID'),
        ),
        migrations.AddField(
            model_name='troublegroup',
            name='num_created_child',
            field=models.IntegerField(default=0, verbose_name='子Groupの数'),
        ),
        migrations.AddField(
            model_name='troublegroup',
            name='path',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='分類ツリー経路'),
        ),
    ]
