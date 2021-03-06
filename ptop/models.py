"""PTOP Model Module"""

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
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
#        email = self.normalize_email(email)
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

    objects = CustomUserManager()

    # 平たくいうと上からメールドレスフィールド、ユーザー名として使うフィールド、スーパーユーザーを作る際に必ず入力するべきフィールドを指定している。
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELD = ['email']

#	class Meta:
#		verbose_name = _('user')
#		verbose_name_plural = _('users')

    # メールの送信に関するメソッド
#    def email_user(self, subject, message, from_email=None, **kwargs):
#        send_mail(subject, message, from_email, [self.email], **kwargs)

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
        return self.start_time.strftime('%Y%m%m-%H%M%S') + '_' + self.operation_type.name

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
    errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ', null=True, blank=True)
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
        events = self.troubleevent_set.order_by('start_time')
        return events[0]

    def num_events(self):
        '''イベント数を返すメソッド'''
        return self.troubleevent_set.count()

    def average_downtime(self):
        '''平均停止時間を返すメソッド'''
        return list(self.troubleevent_set.aggregate(models.Avg('downtime')).values())[0]


class TroubleEvent(models.Model):
    """トラブル事象モデル"""
    title = models.CharField('トラブル名称', max_length=200)
    group = models.ForeignKey(
        TroubleGroup, verbose_name='トラブル分類',
        blank=True, null=True, on_delete=models.SET_NULL)
#	deviceid = models.CharField('device id',max_length=100, null=True, blank=True)
    device = models.ForeignKey(
        Device, verbose_name='デバイス',
        null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField('内容', null=True)
    trigger = models.TextField('発生時の操作', null=True, blank=True)
    cause = models.TextField('原因と状況', null=True, blank=True)
    temporary_action = models.TextField('応急処置内容', null=True, blank=True)
#	error_message = models.CharField('エラーメッセージ',max_length=100, blank=True)
    errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ', null=True, blank=True)
    start_time = models.DateTimeField('発生時刻', null=True)
    end_time = models.DateTimeField('運転再開時刻', null=True, blank=True)
    complete_time = models.DateTimeField('復旧完了時刻', null=True, blank=True)
    downtime = models.PositiveIntegerField('運転停止時間', null=True, blank=True) # 分
    operation_type = models.ForeignKey(
        OperationType, verbose_name='発生時の運転内容',
        null=True, blank=True, on_delete=models.SET_NULL)
    delaytime = models.PositiveIntegerField('治療遅延時間', null=True, blank=True) # 分
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
#        User, verbose_name='入力者', limit_choices_to=((Q(groups__name='Operator')|Q(groups__name='Physicist'))&Q(is_active=True)),
        User, verbose_name='入力者',
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    handling_operators = models.ManyToManyField(
#        User, verbose_name='対応者', limit_choices_to=((Q(groups__name='Operator')|Q(groups__name='Physicist'))&Q(is_active=True)),
        User, verbose_name='対応者',
        blank=True)
    approval_operator = models.ForeignKey(
        User, verbose_name='承認者',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_approved')
    reported_physicist = models.ForeignKey(
        User, verbose_name='報告した物理士',
        limit_choices_to=Q(groups__name='Physicist')&Q(is_active=True),
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
        TroubleGroup, verbose_name='投稿先のトラブル類型', null=True, on_delete=models.CASCADE)
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

    def clean(self):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.name)
                if value:
                    setattr(self, field.name, standardize_character(value))

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
