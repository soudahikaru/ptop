# Generated by Django 3.0.3 on 2021-03-23 02:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0026_historicaltroubleevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltroubleevent',
            name='created_on',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='historicaltroubleevent',
            name='modified_on',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='troubleevent',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='troubleevent',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='troublegroup',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='troublegroup',
            name='modified_on',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='HistoricalTroubleGroup',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='トラブル分類名称')),
                ('classify_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='分類ID')),
                ('description', models.TextField(null=True, verbose_name='内容')),
                ('trigger', models.TextField(blank=True, null=True, verbose_name='発生の契機となる操作')),
                ('cause', models.TextField(blank=True, null=True, verbose_name='原因')),
                ('first_datetime', models.DateTimeField(blank=True, null=True, verbose_name='初発日時')),
                ('common_action', models.TextField(blank=True, null=True, verbose_name='主要な対処法')),
                ('reminder_datetime', models.DateField(blank=True, null=True, verbose_name='振り返り予定日')),
                ('permanent_action', models.TextField(blank=True, null=True, verbose_name='恒久対策の内容')),
                ('is_common_trouble', models.BooleanField(blank=True, default=False, null=True, verbose_name='よくあるトラブルフラグ')),
                ('criticality_score', models.IntegerField(blank=True, null=True, verbose_name='FMEA致命度スコア')),
                ('frequency_score', models.IntegerField(blank=True, null=True, verbose_name='FMEA発生頻度スコア')),
                ('difficulty_score', models.IntegerField(blank=True, null=True, verbose_name='FMEA対応難度スコア')),
                ('path', models.CharField(blank=True, max_length=50, null=True, verbose_name='分類ツリー経路')),
                ('num_created_child', models.IntegerField(default=0, verbose_name='子Groupの数')),
                ('created_on', models.DateTimeField(blank=True, editable=False)),
                ('modified_on', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('causetype', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.CauseType', verbose_name='原因の類型')),
                ('classify_operator', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='分類作成者')),
                ('device', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.Device', verbose_name='デバイスID')),
                ('handling_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.HandlingStatusType', verbose_name='対処状況')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('vendor_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.VendorStatusType', verbose_name='メーカー連絡状況')),
            ],
            options={
                'verbose_name': 'historical trouble group',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
