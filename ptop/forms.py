"""PTOP Form Module"""

from datetime import datetime
from django.contrib.admin.widgets import FilteredSelectMultiple
import bootstrap_datepicker_plus as datetimepicker
from dal import autocomplete
from django.core import validators
from django import forms
from django.urls import reverse_lazy
from django.utils import timezone
from .models import TroubleEvent, Device, Error
from .models import TroubleGroup
from .models import User
from .models import Attachment
from .models import Announcement
from .models import Comment, CommentType
from .models import Operation, OperationType, OperationMetaType
from .models import CauseType, VendorStatusType, HandlingStatusType

class AttachmentForm(forms.ModelForm):
    """Attachmentを作るForm"""
    class Meta:
        model = Attachment
        fields = ('file',)

class StatisticsForm(forms.Form):
    """統計算出Form"""
    date_s = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).start_of('期間'), required=False)
    date_e = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).end_of('期間'), required=False)
    CHOICE = (
        ('day', '日'),
        ('week', '週'),
        ('month', '月'),
        ('year', '年'),
    )
    subtotal_frequency = forms.ChoiceField(
        label='小計単位', widget=forms.RadioSelect, choices=CHOICE, initial='day')

class EventSearchForm(forms.Form):
    """TroubleEventの簡易検索Form"""
    query = forms.CharField(label='キーワード', max_length=100, required=False)

    CHOICE_SORT = (
        ('-start_time', '発生日時が新しい順'),
        ('start_time', '発生日時が古い順'),
        ('-id', '入力日時(id)が新しい順'),
        ('id', '入力日時(id)が古い順'),
        ('-downtime', '故障時間が長い順'),
        ('downtime', '故障時間が短い順'),
        ('-delaytime', '治療遅延時間が長い順'),
        ('delaytime', '治療遅延時間が短い順'),
    )
    sort_by = forms.ChoiceField(choices=CHOICE_SORT, label='並び順', required=False)

    CHOICE_PAGE = (
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
        ('50', '50'),
        ('100', '100'),
    )
    paginate_by = forms.ChoiceField(choices=CHOICE_PAGE, label='1ページの件数', required=False)

class EventAdvancedSearchForm(forms.Form):
    """TroubleEventの詳細検索Form"""
    CHOICE = (
        ('0', ''),
        ('1', ''),
        ('2', ''),
        ('3', ''),
    )
    tuple_noselect = (('NOSELECT', '指定しない'),)
    id = forms.CharField(label='事象ID', max_length=100, required=False)
    title = forms.CharField(label='題名', max_length=100, required=False)
    description = forms.CharField(label='内容', max_length=100, required=False)
    cause = forms.CharField(label='原因や状況', max_length=100, required=False)
    error = forms.CharField(label='エラーメッセージ', max_length=100, required=False)
    device = forms.CharField(label='デバイスID', max_length=100, required=False)
    date_type = forms.ChoiceField(label='', widget=forms.RadioSelect, choices=CHOICE, initial='0')
    date_delta1 = forms.IntegerField(
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    date2 = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d', options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}),
        required=False)
    date_delta2 = forms.IntegerField(
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    date3s = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).start_of('期間'), required=False)
    date3e = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).end_of('期間'), required=False)
#	print(tuple_noselect+TroubleGroup.VENDOR_STATUS)
    downtime_low = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 0, 'style': 'width:6ch',}),
        validators=[validators.MinValueValidator(0)], required=False)
    downtime_high = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 0, 'style': 'width:6ch',}),
        validators=[validators.MinValueValidator(0)], required=False)
    delaytime_low = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 0, 'style': 'width:6ch',}),
        validators=[validators.MinValueValidator(0)], required=False)
    delaytime_high = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 0, 'style': 'width:6ch',}),
        validators=[validators.MinValueValidator(0)], required=False)
    CHOICE_SORT = (
        ('-start_time', '発生日時が新しい順'),
        ('start_time', '発生日時が古い順'),
        ('-id', '入力日時(id)が新しい順'),
        ('id', '入力日時(id)が古い順'),
        ('-downtime', '故障時間が長い順'),
        ('downtime', '故障時間が短い順'),
        ('-delaytime', '治療遅延時間が長い順'),
        ('delaytime', '治療遅延時間が短い順'),
    )
    sort_by = forms.ChoiceField(choices=CHOICE_SORT, label='並び順', required=False)

    CHOICE_PAGE = (
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
        ('50', '50'),
        ('100', '100'),
    )
    paginate_by = forms.ChoiceField(choices=CHOICE_PAGE, label='1ページの件数', required=False)

class GroupSearchForm(forms.Form):
    """TroubleGroupの簡易検索Form"""
    query = forms.CharField(label='キーワード', max_length=100, required=False)

    CHOICE_SORT = (
        ('-first_datetime', '発生日時が新しい順'),
        ('first_datetime', '発生日時が古い順'),
        ('-id', '入力日時(id)が新しい順'),
        ('id', '入力日時(id)が古い順'),
    )
    sort_by = forms.ChoiceField(choices=CHOICE_SORT, label='並び順', required=False)

    CHOICE_PAGE = (
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
        ('50', '50'),
        ('100', '100'),
    )
    paginate_by = forms.ChoiceField(choices=CHOICE_PAGE, label='1ページの件数', required=False)

class AdvancedSearchForm(forms.Form):
    """TroubleGroupの詳細検索Form"""
    CHOICE = (
        ('0', ''),
        ('1', ''),
        ('2', ''),
        ('3', ''),
    )
    tuple_noselect = (('NOSELECT', '指定しない'),)
    classify_id = forms.CharField(label='分類ID', max_length=100, required=False)
    title = forms.CharField(label='題名', max_length=100, required=False)
    description = forms.CharField(label='内容', max_length=100, required=False)
    cause = forms.CharField(label='原因', max_length=100, required=False)
    error = forms.CharField(label='エラーメッセージ', max_length=100, required=False)
    device = forms.CharField(label='デバイスID', max_length=100, required=False)
    date_type = forms.ChoiceField(label='', widget=forms.RadioSelect, choices=CHOICE, initial='0')
    date_delta1 = forms.IntegerField(
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    date2 = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d', options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}),
        required=False)
    date_delta2 = forms.IntegerField(
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    date3s = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).start_of('期間'), required=False)
    date3e = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d',
            options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}
            ).end_of('期間'), required=False)
#	print(tuple_noselect+TroubleGroup.VENDOR_STATUS)
    causetype = forms.ModelChoiceField(
        CauseType.objects.all(), label='原因類型', required=False, empty_label='指定しない')
    vendor_status = forms.ModelChoiceField(
        VendorStatusType.objects.all(), label='メーカー対応状況', required=False, empty_label='指定しない')
    handling_status = forms.ModelChoiceField(
        HandlingStatusType.objects.all(), label='メーカー対応状況', required=False, empty_label='指定しない')

    CHOICE_SORT = (
        ('-first_datetime', '発生日時が新しい順'),
        ('first_datetime', '発生日時が古い順'),
        ('-id', '入力日時(id)が新しい順'),
        ('id', '入力日時(id)が古い順'),
    )
    sort_by = forms.ChoiceField(choices=CHOICE_SORT, label='並び順', required=False)

    CHOICE_PAGE = (
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
        ('50', '50'),
        ('100', '100'),
    )
    paginate_by = forms.ChoiceField(choices=CHOICE_PAGE, label='1ページの件数', required=False)

class EventCreateForm(forms.ModelForm):
    """TroubleEventの新規作成Form"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={'size':80}), label='トラブル題名', required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='内容', required=True)
    trigger = forms.CharField(
        widget=forms.Textarea(attrs={'rows':2, 'cols':80}), label='発生直前の操作', required=False)
    cause = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='原因や状況', required=False)
    temporary_action = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='応急処置', required=False)

    start_time = forms.DateTimeField(
        widget=datetimepicker.DateTimePickerInput(
            options={'format':'YYYY-MM-DD HH:mm', 'sideBySide':True}),
        label='発生時刻', required=True)
    end_time = forms.DateTimeField(
        widget=datetimepicker.DateTimePickerInput(
            options={'format':'YYYY-MM-DD HH:mm', 'sideBySide':True}),
        label='復旧時刻', help_text='未入力の場合、装置故障時間を入力すると自動的に入力されます。',
        required=True)
#	end_time = forms.DateTimeField(label='復旧時刻', help_text='空欄の場合、装置故障時間を入力すると自動的に入力されます。', required=True)
    downtime = forms.IntegerField(
        label='装置故障時間(分)', help_text='実際に装置運転に影響があった時間を入力してください。未入力の場合、復旧時刻を入力すると自動的に入力されます。', required=True, 
        widget=forms.NumberInput(attrs={'style': 'width:8ch','min': 0, }),
        validators=[validators.MinValueValidator(0)])
    delaytime = forms.IntegerField(
        label='治療遅延時間(分)', help_text='未入力の場合、運転状況が「治療」で装置故障時間が(自動でも)入力されると自動的に入力されます。', required=True, 
        widget=forms.NumberInput(attrs={'style': 'width:8ch','min': 0, }),
        validators=[validators.MinValueValidator(0)])
    delay_flag = forms.BooleanField(
        label='治療遅延の有無', help_text='治療遅延時間が未入力の場合、運転状況が「治療」で装置故障時間が(自動でも)入力されると自動的にONになります。実際には遅延しなかった場合は手動でOFFにしてください。', required=False)
    operation_type = forms.ModelChoiceField(
        OperationType.objects.all(),
        widget=forms.Select(attrs={'style':'pointer-events: none;', 'tabindex':'-1'}),
        label='運転状況', help_text='発生日時から自動的に設定されます。', required=False)
    device = forms.ModelChoiceField(
        Device.objects.all(), label='デバイスID',
        widget=autocomplete.ModelSelect2(url='ptop:device_autocomplete', attrs={'style':'width:40em;'}),
        help_text='デバイスIDを部分一致検索します。', required=True)
    errors = forms.ModelMultipleChoiceField(
        Error.objects.all(), label='エラーメッセージ',
        widget=autocomplete.ModelSelect2Multiple(url='ptop:error_autocomplete'),
        help_text='エラーメッセージを部分一致検索します。空白部をクリックまたはTab→キー入力で複数選択可能。',
        required=False)
    attachments = forms.ModelMultipleChoiceField(
        Attachment.objects.all(), label='添付ファイル', required=False, 
        widget=forms.SelectMultiple(attrs={'style':'display:none;'}),
        help_text='このウィンドウにファイルをDrag and Dropしてもアップロードできます')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['operation_type'].widget.attrs['readonly'] = True
        print('init queryset')
        print(TroubleEvent.objects.filter(pk=kwargs.get('pk')))
#        self.fields['attachments'].queryset = Attachment.objects.filter(id__in=TroubleEvent.objects.filter(pk=kwargs.get('pk')))

    def clean_attachments(self):
        # 何もチェックせず返す
        print('validation')
        print(self.cleaned_data['attachments'])
        return self.cleaned_data['attachments']

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data.get('start_time'))
        if cleaned_data.get('start_time') > cleaned_data.get('end_time'):
            print(cleaned_data.get('end_time'))
            raise forms.ValidationError("復旧日時は発生日時より後にしてください。")
        super().clean()

#    def __init__(self, *args, **kwargs):
#        self.attachments = kwargs.pop('attachments')
#        super(EventCreateForm, self).__init__(*args, **kwargs)
#        self.fields['attachments'].queryset = Attachment.objects.filter(id__in=self.attachments)

    class Meta:
        model = TroubleEvent
        fields = (
            'title', 'group', 'device',
            'description', 'trigger', 'cause', 'temporary_action', 'errors',
            'start_time', 'downtime', 'operation_type', 'end_time', 'delay_flag', 'delaytime',
            'input_operator', 'handling_operators', 'reported_physicist', 'attachments')

class GroupCreateForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'size':80}), label='トラブル類型題名', required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='内容', required=True)
    trigger = forms.CharField(
        widget=forms.Textarea(attrs={'rows':2, 'cols':80}), label='発生の契機となる操作', required=False)
    cause = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='原因', required=False)
    common_action = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='主要な対処法', required=False)
    permanent_action = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='恒久対策', required=False)

    device = forms.ModelChoiceField(
        Device.objects.all(), label='デバイスID',
        widget=autocomplete.ModelSelect2(url='ptop:device_autocomplete', attrs={'style':'width:40em;'}),
        help_text='デバイスIDを部分一致検索します。', required=True)
    errors = forms.ModelMultipleChoiceField(
        Error.objects.all(), label='エラーメッセージ',
        widget=autocomplete.ModelSelect2Multiple(url='ptop:error_autocomplete'),
        help_text='エラーメッセージを部分一致検索します。空白部をクリックまたはTab→キー入力で複数選択可能。',
        required=False)
    attachments = forms.ModelMultipleChoiceField(
        Attachment.objects.all(), label='添付ファイル', required=False, 
        widget=forms.SelectMultiple(attrs={'style':'display:none;'}),
        help_text='このウィンドウにファイルをDrag and Dropしてもアップロードできます')
    is_common_trouble = forms.BooleanField(
        help_text='チェックするとトップページのよくあるトラブルに登録され、再発事象の入力が簡単になります',
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['path'].widget.attrs['readonly'] = 'readonly'

    class Meta:
        model = TroubleGroup
        fields = (
            'title', 'device', 'description', 'trigger', 'cause', 'causetype',
            'common_action', 'permanent_action', 'errors',
            'handling_status', 'vendor_status',
            'first_datetime', 'reminder_datetime', 'is_common_trouble',
            'criticality_score', 'frequency_score', 'difficulty_score',
            'path', 'classify_operator', 'attachments')

class OperationCreateForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=datetimepicker.DateTimePickerInput(
            options={'format':'YYYY-MM-DD HH:mm', 'sideBySide':True}),
        label='開始時刻', required=True)
    end_time = forms.DateTimeField(
        widget=datetimepicker.DateTimePickerInput(
            options={'format':'YYYY-MM-DD HH:mm', 'sideBySide':True}),
        label='終了時刻', required=True)

    def save(self, commit=True):
        m = super(OperationCreateForm, self).save(commit=False)
        # do custom stuff
        m.operation_time = (m.end_time - m.start_time).total_seconds() / 60.0
        print(m.operation_time)
        if commit:
            m.save()
        return m

    class Meta:
        model = Operation
        fields = (
            'operation_type', 'start_time', 'end_time',
            'num_treat_hc1', 'num_treat_gc2', 'num_qa_hc1', 'num_qa_gc2', 'comment')


class ChangeOperationForm(forms.Form):
    operation_type = forms.ModelChoiceField(queryset=OperationType.objects.all().order_by('id'), label='次のオペレーション')
    change_time = forms.DateTimeField(
        widget=datetimepicker.DateTimePickerInput(
            options={'format':'YYYY-MM-DD HH:mm', 'sideBySide':True}),
        label='切り替え時刻', required=True)

    num_treat_hc1 = forms.IntegerField(initial=0, label='HC1治療ポート数',
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    num_treat_gc2 = forms.IntegerField(initial=0, label='GC2治療ポート数',
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    num_qa_hc1 = forms.IntegerField(initial=0, label='HC1 QAポート数',
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    num_qa_gc2 = forms.IntegerField(initial=0, label='GC2 QAポート数',
        widget=forms.NumberInput(attrs={'style': 'width:6ch','min': 0, }),
        validators=[validators.MinValueValidator(0)], required=False)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols':'60', 'rows':'4'}),
        label='コメント', required=False)

    
class AnnouncementCreateForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'size':80}), label='題名', required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='内容', required=True)
    user = forms.ModelChoiceField(
        User.objects.all(),
        widget=forms.Select(attrs={'style':'pointer-events: none;', 'tabindex':'-1'}),
        label='作成者', help_text='ログインユーザのみ設定可能です。', required=False)

    class Meta:
        model = Announcement
        fields = (
            'title', 'description', 'user')

class CommentCreateForm(forms.ModelForm):
    posted_group = forms.ModelChoiceField(
        TroubleGroup.objects.all(),
        widget=forms.Select(attrs={'style':'pointer-events: none;', 'tabindex':'-1'}),
        label='投稿先のトラブル類型', help_text='変更不可', required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':4, 'cols':80}), label='内容', required=True)
    comment_type = forms.ModelChoiceField(
        CommentType.objects.all(),
        label='コメントの種類', required=False)
    user = forms.ModelChoiceField(
        User.objects.all(),
        widget=forms.Select(attrs={'style':'pointer-events: none;', 'tabindex':'-1'}),
        label='作成者', help_text='自動的にログインユーザとなります。', required=False)
    attachments = forms.ModelMultipleChoiceField(
        Attachment.objects.all(), label='添付ファイル', required=False, 
        widget=forms.SelectMultiple(attrs={'style':'display:none;'}),
        help_text='このウィンドウにファイルをDrag and Dropしてもアップロードできます')

    class Meta:
        model = Announcement
        fields = (
            'posted_group', 'description', 'comment_type', 'user', 'attachments')
