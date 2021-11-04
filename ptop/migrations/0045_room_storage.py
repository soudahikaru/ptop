# Generated by Django 3.2.6 on 2021-11-02 03:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0044_auto_20211029_1700'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='部屋名称')),
                ('floor', models.CharField(max_length=100, verbose_name='階数')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='保管場所名称')),
                ('place_list', models.CharField(max_length=300, verbose_name='段数リスト')),
                ('x', models.FloatField(blank=True, null=True, verbose_name='x座標')),
                ('y', models.FloatField(blank=True, null=True, verbose_name='y座標')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ptop.room', verbose_name='部屋')),
            ],
        ),
    ]
