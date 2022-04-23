"""PTOP Model Module"""

import datetime
import numpy as np

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import EmailValidator
# from django.utils.translation import gettext_lazy as _
# from django.utils import timezone
from simple_history.models import HistoricalRecords
import jaconv

# Create your models here.


def standardize_character(str):
    """文字表記ゆれを統一する関数(カナは全角、英数字と記号は半角に変換)"""
    str = jaconv.z2h(str, kana=False, digit=True, ascii=True)
    str = jaconv.h2z(str, kana=True, digit=False, ascii=False)
    return str


class CustomUserManager(UserManager):
    """ユーザーマネージャー"""
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        username = self.model.normalize_username(username)
        # email = self.normalize_email(email)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Userモデル"""

    AUTHORITIES = (
        (0, '一般オペレータ'),
        (1, 'チーフオペレータ'),
        (2, 'システム管理者'),
    )

    EXPERIENCES = (
        (0, '新人'),
        (1, '一般'),
        (2, 'ベテラン')
    )

    # Userモデルの基本項目。
    username = models.CharField(max_length=30, unique=True)
    last_name = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True, validators=[EmailValidator('Invalid email address.')])
    phs_number = models.CharField(blank=True, max_length=10)

    display_order = models.IntegerField(null=True, blank=True)

    # 拡張項目
    authority_level = models.IntegerField(choices=AUTHORITIES, null=True)
    experience_level = models.IntegerField(choices=EXPERIENCES, null=True)
    date_joined = models.DateField(null=True)
    date_expired = models.DateField(blank=True, null=True)

    def __str__(self):
        if self.last_name:
            return self.last_name + ' ' + self.first_name
        else:
            return self.username

    # adminサイトへのアクセス権をユーザーが持っているか判断するメソッド
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether this user can log into this admin site.',
    )

    # ユーザーがアクティブかどうか判断するメソッド
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active. \
            Unselect this instead of deleting accounts.'
    )

    # 不具合連絡票送信先かどうかのフラグ
    is_tcs_destination = models.BooleanField(
        default=False,
        help_text='不具合連絡票送信先に含める'
    )

    objects = CustomUserManager()

    # 平たくいうと上からメールドレスフィールド、ユーザー名として使うフィールド、スーパーユーザーを作る際に必ず入力するべきフィールドを指定している。
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELD = ['email']

    def fullname(self):
        return '%s %s' % (self.last_name, self.first_name)


#   メールの送信に関するメソッド
#   def email_user(self, subject, message, from_email=None, **kwargs):
#       send_mail(subject, message, from_email, [self.email], **kwargs)


class Operator(models.Model):
    """Operatorモデル(旧ver)"""
    AUTHORITIES = (
        (0, '一般オペレータ'),
        (1, 'チーフオペレータ'),
        (2, 'システム管理者'),
    )

    EXPERIENCES = (
        (0, '新人'),
        (1, '一般'),
        (2, 'ベテラン')
    )

    name = models.CharField(max_length=100)
    authority_level = models.IntegerField(choices=AUTHORITIES)
    experience_level = models.IntegerField(choices=EXPERIENCES)
    registered_date = models.DateField(null=False)
    expired_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SuperSection(models.Model):
    """上位Sectionモデル。装置の各機器を管理する。"""
    name = models.CharField('名称', max_length=100)

    def __str__(self):
        return self.name


class Section(models.Model):
    """Sectionモデル。装置の設置領域を管理する。"""
    name = models.CharField('名称', max_length=100)
    super_section = models.ForeignKey(
        SuperSection, verbose_name='上位セクション', null=True, blank=True,
        on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    """DeviceTypeモデル。Deviceの種類を管理する。"""
    name = models.CharField('名称', max_length=100)

    def __str__(self):
        return self.name


class Device(models.Model):
    """Deviceモデル。装置の各機器を管理する。"""
    device_id = models.CharField('デバイスID', max_length=30, unique=True)
    name = models.CharField('デバイス名称', max_length=100)
    section = models.ForeignKey(
        Section, verbose_name='装置セクション', null=True, blank=True,
        on_delete=models.SET_NULL)
    device_type = models.ForeignKey(
        DeviceType, verbose_name='デバイス種類', null=True, blank=True,
        on_delete=models.SET_NULL)

    def __str__(self):
        return self.device_id

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))


class Error(models.Model):
    """Errorモデル。エラーコードとエラーの説明を管理する。"""
    error_code = models.CharField('エラーコード', max_length=100, unique=True)
    error_description = models.CharField('エラー説明', max_length=200, null=True, blank=True)

    def __str__(self):
        return self.error_code

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))


class Attachment(models.Model):
    """添付ファイルモデル"""
    title = models.CharField('ファイル名', max_length=200, null=True)
    description = models.CharField('説明', max_length=200, null=True)
    file = models.FileField(upload_to='attachments/', null=True)
    uploaded_datetime = models.DateTimeField('ファイル', null=True)

    def __str__(self):
        return self.title


class OperationMetaType(models.Model):
    """Operationのメタ型。OperationTypeをさらに集約する。"""
    name = models.CharField('メタ運転タイプ名称', max_length=100)

    def __str__(self):
        return self.name


class OperationType(models.Model):
    """OperationのType。治療、QAなど。"""
    name = models.CharField('運転タイプ名称', max_length=100)
    meta_type = models.ForeignKey(
        OperationMetaType, verbose_name='メタ運転タイプ', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class TreatmentStatusType(models.Model):
    """装置不具合連絡票用の治療可能かどうかのタイプ。"""
    name = models.CharField('治療可否タイプ名称', max_length=100)
    treatment_available_flag = models.BooleanField('治療可ならTrue')

    def __str__(self):
        return self.name


class EffectScope(models.Model):
    """影響範囲モデル。"""
    name = models.CharField('影響範囲名称', max_length=100)
    hc1_flag = models.BooleanField('HC1に影響があればTrue')
    gc2_flag = models.BooleanField('GC2に影響があればTrue')

    def __str__(self):
        return self.name


class RequireType(models.Model):
    """要望項目モデル。"""
    name = models.CharField('項目名称', max_length=100)
    display_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Urgency(models.Model):
    """対処緊急性モデル。"""
    name = models.CharField('緊急性名称', max_length=100)

    def __str__(self):
        return self.name


class CauseType(models.Model):
    """TroubleGroupの原因のType。経年劣化、偶発故障など。"""
    name = models.CharField('原因タイプ名称', max_length=100)

    def __str__(self):
        return self.name


class VendorStatusType(models.Model):
    """TroubleGroupのメーカー報告状況のType。未連絡、連絡済みなど。"""
    name = models.CharField('メーカー報告状況名称', max_length=100)

    def __str__(self):
        return self.name


class HandlingStatusType(models.Model):
    """TroubleGroupの対応状況のType。様子見、修理予定など。"""
    name = models.CharField('対応状況名称', max_length=100)

    def __str__(self):
        return self.name


class Operation(models.Model):
    """Operationモデル。運転業務の開始終了時刻と内容を管理する。"""
    operation_type = models.ForeignKey(
        OperationType, verbose_name='運転タイプ',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    start_time = models.DateTimeField('開始日時', null=True)
    end_time = models.DateTimeField('終了日時', null=True, blank=True)
    operation_time = models.PositiveIntegerField('運転時間', null=True, blank=True)
    num_treat_hc1 = models.IntegerField('HC1 治療ポート数', null=True, blank=True)
    num_treat_gc2 = models.IntegerField('GC2 治療ポート数', null=True, blank=True)
    num_qa_hc1 = models.IntegerField('HC1 QAポート数', null=True, blank=True)
    num_qa_gc2 = models.IntegerField('GC2 QAポート数', null=True, blank=True)
    comment = models.TextField('コメント', null=True, blank=True)

    def __str__(self):
        return self.start_time.strftime('%Y%m%d-%H%M%S') + '_' + self.operation_type.name


class TroubleGroup(models.Model):
    """トラブル類型モデル"""

    CAUSETYPES = (
        ('CT_ACC', '偶発故障'),
        ('CT_DET', '経年劣化'),
        ('CT_OPE', 'オペミス'),
        ('CT_INI', '初期不良'),
        ('CT_DES', '設計不良'),
        ('CT_MAN', '製作不良')
    )

    VENDOR_STATUS = (
        ('VS_NON', '連絡不要'),
        ('VS_YET', '未連絡'),
        ('VS_RWA', '連絡済み回答待ち'),
        ('VS_RPL', '連絡済み対処予定'),
        ('VS_RPL', '連絡済み様子見'),
        ('VS_FIN', '対処完了')
    )

    HANDLING_STATUS = (
        ('HS_IGN', '放置可能'),
        ('HS_YET', '未対策'),
        ('HS_SEE', '様子見'),
        ('HS_WAT', '重点監視'),
        ('HS_AVO', '運用回避'),
        ('HS_VEN', 'メーカー依頼中'),
        ('HS_FIN', '解決済')
    )

    title = models.CharField('トラブル分類名称', max_length=200)
    classify_id = models.CharField('分類ID', max_length=50, null=True, blank=True)
    device = models.ForeignKey(
        Device, verbose_name='デバイスID',
        blank=True, null=True, on_delete=models.SET_NULL)
    description = models.TextField('内容', null=True)
    trigger = models.TextField('発生の契機となる操作', null=True, blank=True)
    cause = models.TextField('原因', null=True, blank=True)
    first_datetime = models.DateTimeField('初発日時', null=True, blank=True)
    common_action = models.TextField('主要な対処法', null=True, blank=True)
#    causetype = models.CharField('原因の類型', choices=CAUSETYPES, max_length=20, null=True, blank=True)
    causetype = models.ForeignKey(
        CauseType, verbose_name='原因の類型', null=True, blank=True, on_delete=models.SET_NULL)
    errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ', blank=True)
    classify_operator = models.ForeignKey(
        User, verbose_name='分類作成者', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='%(class)s_classified')
    handling_status = models.ForeignKey(
        HandlingStatusType, verbose_name='対処状況', null=True, blank=True, on_delete=models.SET_NULL)
#    handling_status = models.CharField(
#        '対処状況', choices=HANDLING_STATUS, max_length=20, null=True, blank=True)
    vendor_status = models.ForeignKey(
        VendorStatusType, verbose_name='メーカー連絡状況', null=True, blank=True, on_delete=models.SET_NULL)
#    vendor_status = models.CharField(
#        'メーカー連絡状況', choices=VENDOR_STATUS, max_length=20, null=True, blank=True)

    require_items = models.ManyToManyField(
        RequireType, verbose_name='要望項目',
        blank=True)
    require_detail = models.TextField('要望詳細', null=True, blank=True)

    effect_scope = models.ForeignKey(
        EffectScope, verbose_name='影響範囲',
        null=True, blank=True, on_delete=models.SET_NULL)
    treatment_status = models.ForeignKey(
        TreatmentStatusType, verbose_name='発生中の治療可否状況',
        null=True, blank=True, on_delete=models.SET_NULL)
    urgency = models.ForeignKey(
        Urgency, verbose_name='対処緊急性',
        null=True, blank=True, on_delete=models.SET_NULL)

    reminder_datetime = models.DateField('振り返り予定日', null=True, blank=True)
    permanent_action = models.TextField('恒久対策の内容', null=True, blank=True)
    is_common_trouble = models.BooleanField('よくあるトラブルフラグ', default=False, null=True, blank=True)
    criticality_score = models.IntegerField('FMEA致命度スコア', null=True, blank=True)
    frequency_score = models.IntegerField('FMEA発生頻度スコア', null=True, blank=True)
    difficulty_score = models.IntegerField('FMEA対応難度スコア', null=True, blank=True)
    path = models.CharField('分類ツリー経路', max_length=50, null=True, blank=True)
    num_created_child = models.IntegerField('子Groupの数', default=0)
    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.title

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))

    def first_event(self):
        '''初発イベントを返すメソッド'''
        if self.num_events() > 0:
            events = self.troubleevent_set.order_by('start_time')
            return events[0]
        else:
            return None

    def num_events(self):
        '''イベント数を返すメソッド'''
        return self.troubleevent_set.count()

    def average_downtime(self):
        '''平均停止時間を返すメソッド'''
        if self.num_events() > 0:
            return list(self.troubleevent_set.aggregate(models.Avg('downtime')).values())[0]
        else:
            return 0

    def new_comment(self):
        '''最新コメントを返すメソッド'''
        if self.comments.count() > 0:
            comments = self.comments.order_by('-posted_on')
            return comments[0]
        else:
            return None


class TroubleEvent(models.Model):
    """トラブル事象モデル"""
    title = models.CharField('トラブル名称', max_length=200)
    group = models.ForeignKey(
        TroubleGroup, verbose_name='トラブル分類',
        blank=True, null=True, on_delete=models.SET_NULL)
    # deviceid = models.CharField('device id',max_length=100, null=True, blank=True)
    device = models.ForeignKey(
        Device, verbose_name='デバイス',
        null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField('内容', null=True)
    trigger = models.TextField('発生時の操作', null=True, blank=True)
    cause = models.TextField('原因と状況', null=True, blank=True)
    temporary_action = models.TextField('応急処置内容', null=True, blank=True)
    # error_message = models.CharField('エラーメッセージ',max_length=100, blank=True)
    errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ', blank=True)
    start_time = models.DateTimeField('発生時刻', null=True)
    end_time = models.DateTimeField('運転再開時刻', null=True, blank=True)
    complete_time = models.DateTimeField('復旧完了時刻', null=True, blank=True)
    downtime = models.PositiveIntegerField('運転停止時間', null=True, blank=True)  # 分
    operation_type = models.ForeignKey(
        OperationType, verbose_name='発生時の運転内容',
        null=True, blank=True, on_delete=models.SET_NULL)
    delaytime = models.PositiveIntegerField('治療遅延時間', null=True, blank=True)  # 分
    delay_flag = models.BooleanField('治療遅延の有無', default=False)
    effect_scope = models.ForeignKey(
        EffectScope, verbose_name='影響範囲',
        null=True, blank=True, on_delete=models.SET_NULL)
    treatment_status = models.ForeignKey(
        TreatmentStatusType, verbose_name='発生中の治療可否状況',
        null=True, blank=True, on_delete=models.SET_NULL)
    urgency = models.ForeignKey(
        Urgency, verbose_name='対処緊急性',
        null=True, blank=True, on_delete=models.SET_NULL)

    input_operator = models.ForeignKey(
        User, verbose_name='入力者',
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    handling_operators = models.ManyToManyField(
        User, verbose_name='対応者',
        blank=True)
    approval_operator = models.ForeignKey(
        User, verbose_name='承認者',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_approved')
    reported_physicist = models.ForeignKey(
        User, verbose_name='報告した物理士',
        limit_choices_to=Q(groups__name='Physicist') & Q(is_active=True),
        null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_reported')
    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.title

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))


class CommentType(models.Model):
    """コメントタイプモデル"""
    name = models.CharField('コメントタイプ名称', max_length=100)

    def __str__(self):
        return self.name


class Comment(models.Model):
    """コメントモデル"""
    posted_group = models.ForeignKey(
        TroubleGroup, verbose_name='投稿先のトラブル類型', null=True, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', verbose_name='親コメント', null=True, blank=True, on_delete=models.CASCADE)

    description = models.TextField('文章', null=True)
    comment_type = models.ForeignKey(
        CommentType, verbose_name='コメントタイプ',
        null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(
        User, verbose_name='入力者', limit_choices_to=Q(is_active=True),
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    posted_on = models.DateTimeField('作成時刻', auto_now_add=True)
    modified_on = models.DateTimeField('更新時刻', auto_now=True)

    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)

    @property
    def is_modified(self):
        delta = self.modified_on - self.posted_on
        if delta > datetime.timedelta(minutes=1):
            return True
        else:
            return False

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))

    def __str__(self):
        return '%s%s_%s' % (self.user.last_name, self.user.first_name, self.posted_on.strftime('%Y/%m/%d-%H:%M'))


class Announcement(models.Model):
    """お知らせモデル"""
    title = models.CharField('題名', max_length=200, null=True)
    description = models.TextField('内容', null=True)
    user = models.ForeignKey(
        User, verbose_name='作成者', limit_choices_to=Q(is_active=True),
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    posted_time = models.DateTimeField('作成時刻', auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))


class EmailAddress(models.Model):
    email = models.EmailField(blank=False, validators=[EmailValidator('Invalid email address.')])
    is_tcs_destination = models.BooleanField(
        default=True,
        help_text='不具合連絡票送信先に含める'
    )
    display_order = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.email


class TroubleCommunicationSheet(models.Model):
    """不具合連絡票モデル"""
    group = models.ForeignKey(
        TroubleGroup, verbose_name='トラブル類型', null=False, blank=False,
        on_delete=models.CASCADE)
    version = models.PositiveIntegerField(null=False, blank=False)

    user = models.ForeignKey(
        User, verbose_name='発行者', null=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='trouble_communication_sheet/', null=True)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.group.classify_id}-ver{self.version}'


class Room(models.Model):
    """部屋モデル"""
    name = models.CharField('部屋名称', max_length=100, null=False, blank=False)
    floor = models.CharField('階数', max_length=100, null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.floor}{self.name}'


class Storage(models.Model):
    """保管場所モデル"""
    room = models.ForeignKey(Room, verbose_name='部屋', null=False, blank=False, on_delete=models.CASCADE)
    name = models.CharField('保管場所名称', max_length=100, null=False, blank=False)
    num_subplace = models.IntegerField('段数', null=False, blank=False, default=0)
    x = models.FloatField('x座標', null=True, blank=True)
    y = models.FloatField('y座標', null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def fullname(self):
        return f"{self.room.floor}{self.room.name}_{self.name}"

    def __str__(self):
        return f"{self.room.floor}{self.room.name}_{self.name}"


class SupplyType(models.Model):
    """消耗品形式モデル"""
    name = models.CharField('名称', max_length=100, null=False, blank=False, default='')
    vendor_name = models.CharField('メーカー名', max_length=100, null=False, blank=False, default='')
    model_number = models.CharField('型式番号', max_length=100, null=False, blank=False, default='')
    level_name = models.CharField('残量指標の名称', max_length=100, null=False, blank=False, default='')
    level_unit = models.CharField('残量指標の単位', max_length=100, null=True, blank=True, default='')
    initial_level = models.FloatField('デフォルト初期残量', null=False, blank=False)
    warning_level = models.FloatField('警告レベル', null=False, blank=False)
    exchange_level = models.FloatField('交換目標レベル', null=False, blank=False)
    fault_level = models.FloatField('機能停止レベル', null=False, blank=False)
    estimation_method = models.CharField('寿命予測方法', max_length=10, null=False, blank=False, default='linear')
    num_recommend = models.PositiveIntegerField('推奨在庫数', null=False, blank=False)
    candidate_devices = models.ManyToManyField(Device, verbose_name='使用するデバイス', blank=False)
    candidate_storage = models.ManyToManyField(Storage, verbose_name='保管場所', blank=False)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def fullscale(self):
        return abs(self.initial_level - self.fault_level)

    def num_stock(self):
        return self.supplyitem_set.filter(is_available=True).count()

    def num_ordered(self):
        return self.supplyitem_set.filter(order_date__isnull=False, stock_date__isnull=True).count()

    def num_used(self):
        return self.supplyitem_set.filter(uninstall_date__isnull=False, dispose_date__isnull=True).count()

    def __str__(self):
        return self.name


class SupplyItem(models.Model):
    """消耗品個体モデル"""
    supplytype = models.ForeignKey(SupplyType, verbose_name='消耗品形式', null=False, blank=False, on_delete=models.PROTECT)
    installed_device = models.ForeignKey(Device, verbose_name='設置デバイス', null=True, blank=True, on_delete=models.PROTECT)
    storage = models.ForeignKey(Storage, verbose_name='保管場所', null=True, blank=True, on_delete=models.PROTECT)
    serial_number = models.CharField('シリアル番号', max_length=100, null=False, blank=False)
    remain_level = models.FloatField('寿命指標', null=True, blank=True)

    order_date = models.DateTimeField('発注日', null=True, blank=False)
    due_date = models.DateTimeField('納品予定日', null=True, blank=True)
    stock_date = models.DateTimeField('納品日', null=True, blank=True)
    install_date = models.DateTimeField('使用開始日', null=True, blank=True)
    uninstall_date = models.DateTimeField('使用終了日', null=True, blank=True)
    dispose_date = models.DateTimeField('廃棄日', null=True, blank=True)

    is_installed = models.BooleanField('使用中フラグ', default=False)
    is_available = models.BooleanField('使用可能フラグ', default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def current_level(self):
        newest_record = self.supplyrecord_set.all().order_by('-date').first()
        if newest_record:
            return newest_record.level
        else:
            return None

    def percent_level(self):
        if self.current_level() is None:
            return None
        if self.supplytype.initial_level > self.supplytype.exchange_level:
            # 測定値が減少していくもの
            pl = 100.0 * self.current_level() / (self.supplytype.initial_level - self.supplytype.exchange_level)
            print(pl, 'dec')
            return int(pl)
        else:
            pl = 100.0 * (self.supplytype.exchange_level - self.current_level()) / (self.supplytype.exchange_level - self.supplytype.initial_level)
            print(pl, 'dec')
            return int(pl)

    def calc_slope(self, queryset):
        if queryset is None:
            queryset = self.supplyrecord_set.order_by('date')
        queryset_filter = queryset.filter(level__gt=0.01)
        X0 = queryset.values_list('date', flat=True)
        X = queryset_filter.values_list('date', flat=True)
        Y = queryset_filter.values_list('level', flat=True)
        # [x,1]の形にする
        x0 = X0[0].timestamp()
        sec_in_day = 60 * 60 * 24
        X = [(x.timestamp() - x0) / sec_in_day for x in X]
        X = np.array([[value, 1] for value in X])
        X = X.astype(np.float64)
        # a, bにそれぞれの予測値が格納される
        a, b = np.linalg.lstsq(X, Y)[0]
        return (a, b)

    def estimated_expire_date(self):
        queryset = self.supplyrecord_set.order_by('date')
        queryset_filter = queryset.filter(level__gt=0.01)
        if queryset_filter.count() < 2:
            return None
        (a, b) = self.calc_slope(queryset)
        if a == 0.0:
            return None
        delta = (self.supplytype.exchange_level - b) / a
        # print(a, b, delta)
        if delta < 0:
            return None
        elif delta > 365:
            return None

        return queryset.first().date + datetime.timedelta(days=delta)

    def status_string(self):
        s = '不定'
        if self.stock_date is None:
            s = '未納品'
        elif self.is_available:
            s = '使用前'
        elif self.is_installed:
            s = '使用中'
        elif self.dispose_date is None:
            s = '使用済'
        else:
            s = '廃棄済'
        return s

    def __str__(self):
        return self.serial_number


class SupplyRecord(models.Model):
    """消耗品記録モデル"""
    item = models.ForeignKey(SupplyItem, verbose_name='消耗品個体', null=False, blank=False, on_delete=models.PROTECT)
    device = models.ForeignKey(Device, verbose_name='設置デバイス', null=False, blank=False, on_delete=models.PROTECT)
    level = models.FloatField('寿命指標測定結果', null=False, blank=False)
    date = models.DateTimeField('測定日時', null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.supplytype.name}{self.item.serial_number}={self.level}({self.date.strftime('%Y/%m/%d')})"


class ReminderType(models.Model):
    """リマインダー種類モデル"""
    name = models.CharField('名称', max_length=100, null=False, blank=False)
    display_order = models.IntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.name


class Reminder(models.Model):
    """リマインダーモデル"""
    group = models.ForeignKey(TroubleGroup, verbose_name='対象トラブル類型', null=False, blank=False, on_delete=models.CASCADE)
    reminder_type = models.ForeignKey(ReminderType, verbose_name='種類', null=False, blank=False, on_delete=models.PROTECT)
    due_date = models.DateField('期限日', null=False, blank=False)
    description = models.TextField('内容', null=True, blank=True)
    is_done = models.BooleanField('処理済みフラグ', default=False)
    done_datetime = models.DateTimeField('完了日時', null=True, blank=True)
    after_description = models.TextField('処置メモ', null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def state(self):
        if (self.due_date <= timezone.localdate()) and (self.is_done is True):
            return '処理済'
        elif (self.due_date <= timezone.localdate()) and (self.is_done is False):
            return '発動中'
        elif (self.due_date > timezone.localdate()):
            return '期限前'

    def __str__(self):
        return f"{self.group.title}_{self.reminder_type}_{self.due_date.strftime('%Y/%m/%d')}"


class TreatmentRoom(models.Model):
    """治療室モデル"""
    room_id = models.CharField('治療室ID', max_length=100, null=False, blank=False)
    name = models.CharField('名称', max_length=100, null=False, blank=False)
    display_order = models.IntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.name


class IrradiationTechnique(models.Model):
    """照射方式モデル"""
    name = models.CharField('名称', max_length=100, null=False, blank=False)
    display_order = models.IntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.name


class BeamDirection(models.Model):
    """ビーム方向モデル"""
    name = models.CharField('名称', max_length=100, null=False, blank=False)
    display_order = models.IntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.name


class BeamCourse(models.Model):
    """ビームコースモデル"""
    treatment_room = models.ForeignKey(TreatmentRoom, verbose_name='治療室', null=False, blank=False, on_delete=models.CASCADE)
    course_id = models.CharField('コースID', max_length=100, null=False, blank=False)
    name = models.CharField('名称', max_length=100, null=False, blank=False)
    beam_direction = models.ForeignKey(BeamDirection, verbose_name='ビーム方向', null=True, on_delete=models.SET_NULL)
    irradiation_technique = models.ForeignKey(IrradiationTechnique, verbose_name='照射方式', null=True, on_delete=models.SET_NULL)
    is_clinical = models.BooleanField('治療可', default=True)

    display_order = models.IntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.course_id


class OperationResult(models.Model):
    """運転結果モデル"""
    operation = models.ForeignKey(Operation, verbose_name='運転内容', null=False, blank=False, on_delete=models.CASCADE)
    beam_course = models.ForeignKey(BeamCourse, verbose_name='コース', null=False, blank=False, on_delete=models.CASCADE)
    num_complete = models.IntegerField('完遂数', null=False, blank=False, default=0)
    num_canceled_by_patient = models.IntegerField('患者都合中止数', null=False, blank=False, default=0)
    num_canceled_by_machine = models.IntegerField('装置都合中止数', null=False, blank=False, default=0)

    def __str__(self):
        if self.operation.operation_type.name == '患者QA' or self.operation.operation_type.name == '新患測定':
            return f'{self.operation.start_time.strftime("%Y/%m/%d")}_{self.beam_course}_{self.operation.operation_type.name}_正常完了{self.num_complete}/結果不良再測定{self.num_canceled_by_patient}/トラブル起因再測定{self.num_canceled_by_machine}'
        else:
            return f'{self.operation.start_time.strftime("%Y/%m/%d")}_{self.beam_course}_{self.operation.operation_type.name}_完遂{self.num_complete}/患者都合中止{self.num_canceled_by_patient}/装置都合中止{self.num_canceled_by_machine}'
