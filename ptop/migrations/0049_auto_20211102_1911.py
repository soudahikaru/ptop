# Generated by Django 3.2.6 on 2021-11-02 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0048_supplytype_estimation_method'),
    ]

    operations = [
        migrations.RenameField(
            model_name='supplytype',
            old_name='num_recomment',
            new_name='num_recommend',
        ),
        migrations.AlterField(
            model_name='supplytype',
            name='level_name',
            field=models.CharField(default='', max_length=100, verbose_name='残量指標の名称'),
        ),
        migrations.AlterField(
            model_name='supplytype',
            name='level_unit',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='残量指標の単位'),
        ),
    ]
