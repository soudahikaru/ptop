# Generated by Django 3.2.6 on 2021-12-04 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0051_remindertype_display_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='done_datetime',
            field=models.DateTimeField(blank=True, null=True, verbose_name='完了日時'),
        ),
    ]