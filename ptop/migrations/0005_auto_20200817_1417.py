# Generated by Django 3.0.3 on 2020-08-17 05:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0004_auto_20200813_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(max_length=30, verbose_name='デバイスID')),
                ('name', models.CharField(max_length=100, verbose_name='デバイス名称')),
            ],
        ),
        migrations.CreateModel(
            name='ErrorMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=100, verbose_name='エラーメッセージ')),
            ],
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='approval_operator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='troubleevent_approved', to=settings.AUTH_USER_MODEL, verbose_name='承認者'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='cause',
            field=models.TextField(blank=True, null=True, verbose_name='原因'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='delay_flag',
            field=models.BooleanField(default=False, verbose_name='治療遅延の有無'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='delaytime',
            field=models.IntegerField(blank=True, null=True, verbose_name='治療遅延時間'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='description',
            field=models.TextField(null=True, verbose_name='内容'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='device_id',
            field=models.CharField(max_length=100, verbose_name='デバイスID'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='downtime',
            field=models.IntegerField(null=True, verbose_name='装置故障時間'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='復旧時刻'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='handling_operators',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='対応者'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='input_operator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='troubleevent_inputed', to=settings.AUTH_USER_MODEL, verbose_name='入力者'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='start_time',
            field=models.DateTimeField(null=True, verbose_name='発生時刻'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='temporary_action',
            field=models.TextField(blank=True, null=True, verbose_name='応急処置内容'),
        ),
        migrations.AlterField(
            model_name='troubleevent',
            name='title',
            field=models.CharField(max_length=200, verbose_name='題名'),
        ),
    ]
