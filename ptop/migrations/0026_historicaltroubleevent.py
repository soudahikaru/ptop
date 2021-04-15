# Generated by Django 3.0.3 on 2021-03-23 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('ptop', '0025_auto_20210305_1035'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalTroubleEvent',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='トラブル名称')),
                ('description', models.TextField(null=True, verbose_name='内容')),
                ('trigger', models.TextField(blank=True, null=True, verbose_name='発生時の操作')),
                ('cause', models.TextField(blank=True, null=True, verbose_name='原因と状況')),
                ('temporary_action', models.TextField(blank=True, null=True, verbose_name='応急処置内容')),
                ('start_time', models.DateTimeField(null=True, verbose_name='発生時刻')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='復旧時刻')),
                ('downtime', models.PositiveIntegerField(blank=True, null=True, verbose_name='装置故障時間')),
                ('delaytime', models.PositiveIntegerField(blank=True, null=True, verbose_name='治療遅延時間')),
                ('delay_flag', models.BooleanField(default=False, verbose_name='治療遅延の有無')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('approval_operator', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='承認者')),
                ('device', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.Device', verbose_name='デバイス')),
                ('effect_scope', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.EffectScope', verbose_name='影響範囲')),
                ('group', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.TroubleGroup', verbose_name='トラブル分類')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('input_operator', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='入力者')),
                ('operation_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.OperationType', verbose_name='発生時の運転内容')),
                ('reported_physicist', models.ForeignKey(blank=True, db_constraint=False, limit_choices_to=models.Q(('groups__name', 'Physicist'), ('is_active', True)), null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='報告した物理士')),
                ('treatment_status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.TreatmentStatusType', verbose_name='発生中の治療可否状況')),
                ('urgency', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ptop.Urgency', verbose_name='対処緊急性')),
            ],
            options={
                'verbose_name': 'historical trouble event',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
