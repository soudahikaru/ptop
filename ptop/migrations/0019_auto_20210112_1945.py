# Generated by Django 3.0.3 on 2021-01-12 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0018_announcement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='posted_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='作成時刻'),
        ),
    ]
