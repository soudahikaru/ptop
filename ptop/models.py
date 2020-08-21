from django.db import models
from django.db.models import Q
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _

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
	authority_level = models.IntegerField(choices = AUTHORITIES,null=True)
	experience_level = models.IntegerField(choices = EXPERIENCES,null=True)
	date_joined = models.DateField(null=True)
	date_expired = models.DateField(blank=True,null=True)

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
		help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
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
	def email_user(self, subject, message, from_email=None, **kwargs):
		send_mail(subject, message, from_email, [self.email], **kwargs)

class Operator(models.Model):
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
	authority_level = models.IntegerField(choices = AUTHORITIES)
	experience_level = models.IntegerField(choices = EXPERIENCES)
	registered_date = models.DateField(null=False)
	expired_date = models.DateField(blank=True,null=True)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class Device(models.Model):
	device_id = models.CharField('デバイスID', max_length=30)
	name = models.CharField('デバイス名称', max_length=100)
	def __str__(self):
		return self.device_id

class Error(models.Model):
	error_code = models.CharField('エラーコード', max_length=100)
	error_description = models.CharField('エラー説明', max_length=200, null=True,blank=True)
	def __str__(self):
		return self.error_code

class TroubleGroup(models.Model):
	title = models.CharField('トラブル分類名称', max_length=200)
	device = models.ForeignKey(Device, verbose_name='デバイスID', blank=True, null=True, on_delete=models.SET_NULL)
	description = models.TextField('内容', null=True)
	cause = models.TextField('原因',null=True,blank=True)
	def __str__(self):
		return self.title


class TroubleEvent(models.Model):
	title = models.CharField('トラブル名称', max_length=200)
	group = models.ForeignKey(TroubleGroup, verbose_name='トラブル分類', blank=True, null=True, on_delete=models.SET_NULL)
#	deviceid = models.CharField('device id',max_length=100,null=True,blank=True)
	device = models.ForeignKey(Device, verbose_name='デバイス',null=True,blank=True,on_delete=models.SET_NULL)
	description = models.TextField('内容', null=True)
	cause = models.TextField('原因',null=True,blank=True)
	temporary_action = models.TextField('応急処置内容',null=True,blank=True)
#	error_message = models.CharField('エラーメッセージ',max_length=100, blank=True)
	errors = models.ManyToManyField(Error, verbose_name='エラーメッセージ',null=True,blank=True)
	start_time = models.DateTimeField('発生時刻',null=True)
	end_time = models.DateTimeField('復旧時刻',null=True,blank=True)
	downtime = models.IntegerField('装置故障時間',null=True) # 分
	delaytime = models.IntegerField('治療遅延時間',null=True,blank=True) # 分
	delay_flag = models.BooleanField('治療遅延の有無',default=False)
	input_operator = models.ForeignKey(User, verbose_name='入力者', limit_choices_to=Q(groups__name='Operator')&Q(is_active=True), null=True, on_delete=models.SET_NULL,related_name='%(class)s_inputed')
	handling_operators = models.ManyToManyField(User, verbose_name='対応者', limit_choices_to=Q(groups__name='Operator')&Q(is_active=True))
	approval_operator = models.ForeignKey(User, verbose_name='承認者', null=True, blank=True, on_delete=models.SET_NULL,related_name='%(class)s_approved')
	reported_physicist = models.ForeignKey(User, verbose_name='報告した物理士', limit_choices_to=Q(groups__name='Physicist')&Q(is_active=True), null=True, blank=True, on_delete=models.SET_NULL,related_name='%(class)s_reported')
	def __str__(self):
		return self.title

