# Generated by Django 3.0.3 on 2020-12-09 11:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0010_auto_20201202_1742'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='コメントタイプ名称')),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.             Unselect this instead of deleting accounts.'),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(null=True, verbose_name='文章')),
                ('posted_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='発生時刻')),
                ('attachments', models.ManyToManyField(blank=True, to='ptop.Attachment', verbose_name='添付ファイル')),
                ('comment_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ptop.CommentType', verbose_name='コメントタイプ')),
                ('user', models.ForeignKey(limit_choices_to=models.Q(is_active=True), null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comment_inputed', to=settings.AUTH_USER_MODEL, verbose_name='入力者')),
            ],
        ),
    ]
