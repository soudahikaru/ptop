"""PTOP Model Module"""

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Create your models here.

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

class Device(models.Model):
    """Deviceモデル。装置の各機器を管理する。"""
    device_id = models.CharField('デバイスID', max_length=30)
    name = models.CharField('デバイス名称', max_length=100)
    def __str__(self):
        return self.device_id

class Error(models.Model):
    """Errorモデル。エラーコードとエラーの説明を管理する。"""
    error_code = models.CharField('エラーコード', max_length=100)
    error_description = models.CharField('エラー説明', max_length=200, null=True, blank=True)
    def __str__(self):
        return self.error_code

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

class Operation(models.Model):
    """Operationモデル。運転業務の開始終了時刻と内容を管理する。"""
    operation_type = models.ForeignKey(
        OperationType, verbose_name='運転タイプ',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    start_time = models.DateTimeField('開始日時', null=True)
    end_time = models.DateTimeField('終了日時', null=True, blank=True)
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
    causetype = models.CharField('原因の類型', choices=CAUSETYPES, max_length=20, null=True, blank=True)
    errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ', null=True, blank=True)
    classify_operator = models.ForeignKey(
        User, verbose_name='分類作成者', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='%(class)s_classified')
    handling_status = models.CharField(
        '対処状況', choices=HANDLING_STATUS, max_length=20, null=True, blank=True)
    vendor_status = models.CharField(
        'メーカー連絡状況', choices=VENDOR_STATUS, max_length=20, null=True, blank=True)
    reminder_datetime = models.DateField('振り返り予定日', null=True, blank=True)
    permanent_action = models.TextField('恒久対策の内容', null=True, blank=True)
    is_common_trouble = models.BooleanField('よくあるトラブルフラグ', default=False, null=True, blank=True)
    criticality_score = models.IntegerField('FMEA致命度スコア', null=True, blank=True)
    frequency_score = models.IntegerField('FMEA発生頻度スコア', null=True, blank=True)
    difficulty_score = models.IntegerField('FMEA対応難度スコア', null=True, blank=True)
    path = models.CharField('分類ツリー経路', max_length=50, null=True, blank=True)
    num_created_child = models.IntegerField('子Groupの数', default=0)
    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)

    def __str__(self):
        return self.title


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
    end_time = models.DateTimeField('復旧時刻', null=True, blank=True)
    downtime = models.PositiveIntegerField('装置故障時間', null=True) # 分
    operation_type = models.ForeignKey(
        OperationType, verbose_name='発生時の運転内容',
        null=True, blank=True, on_delete=models.SET_NULL)
    delaytime = models.PositiveIntegerField('治療遅延時間', null=True, blank=True) # 分
    delay_flag = models.BooleanField('治療遅延の有無', default=False)
    input_operator = models.ForeignKey(
        User, verbose_name='入力者', limit_choices_to=Q(groups__name='Operator')&Q(is_active=True),
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    handling_operators = models.ManyToManyField(
        User, verbose_name='対応者', limit_choices_to=Q(groups__name='Operator')&Q(is_active=True))
    approval_operator = models.ForeignKey(
        User, verbose_name='承認者',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_approved')
    reported_physicist = models.ForeignKey(
        User, verbose_name='報告した物理士',
        limit_choices_to=Q(groups__name='Physicist')&Q(is_active=True),
        null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_reported')
    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)
    
    def __str__(self):
        return self.title

class CommentType(models.Model):
    """コメントタイプモデル"""
    name = models.CharField('コメントタイプ名称', max_length=100)

    def __str__(self):
        return self.name

class Comment(models.Model):
    """コメントモデル"""
    description = models.TextField('文章', null=True)
    comment_type = models.ForeignKey(
        CommentType, verbose_name='コメントタイプ',
        null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(
        User, verbose_name='入力者', limit_choices_to=Q(is_active=True),
        null=True, on_delete=models.SET_NULL, related_name='%(class)s_inputed')
    posted_time = models.DateTimeField('発生時刻', default=timezone.now)
    attachments = models.ManyToManyField(Attachment, verbose_name='添付ファイル', blank=True)
