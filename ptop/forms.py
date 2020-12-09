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
from .models import Attachment
from .models import Operation, OperationType, OperationMetaType
from .widgets import SuggestWidget

class AttachmentForm(forms.ModelForm):
    """Attachmentを作るForm"""
    class Meta:
        model = Attachment
        fields = ('file',)

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
        widget=forms.NumberInput(attrs={'style': 'width:6ch',}),
        validators=[validators.MinValueValidator(0)], required=False)
    date2 = forms.DateField(
        widget=datetimepicker.DatePickerInput(
            format='%Y-%m-%d', options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM'}),
        required=False)
    date_delta2 = forms.IntegerField(
        widget=forms.NumberInput(attrs={'style': 'width:6ch',}),
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
    causetype = forms.ChoiceField(
        label='原因類型', choices=tuple_noselect+TroubleGroup.CAUSETYPES, required=False)
    vendor_status = forms.ChoiceField(
        label='メーカー対応状況', choices=tuple_noselect+TroubleGroup.VENDOR_STATUS, required=False)
    handling_status = forms.ChoiceField(
        label='対処状況', choices=tuple_noselect+TroubleGroup.HANDLING_STATUS, required=False)

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
        label='装置故障時間', help_text='未入力の場合、復旧時刻を入力すると自動的に入力されます。', required=True)
    delaytime = forms.IntegerField(
        label='治療遅延時間', help_text='未入力の場合、運転状況が「治療」で装置故障時間が(自動でも)入力されると自動的に入力されます。', required=True)
    delay_flag = forms.BooleanField(
        label='治療遅延の有無', help_text='治療遅延時間が未入力の場合、運転状況が「治療」で装置故障時間が(自動でも)入力されると自動的にONになります。実際には遅延しなかった場合は手動でOFFにしてください。', required=False)
    operation_type = forms.ModelChoiceField(
        OperationType.objects.all(),
        widget=forms.Select(attrs={'style':'pointer-events: none;', 'tabindex':'-1'}),
        label='運転状況', help_text='発生日時から自動的に設定されます。', required=False)
    device = forms.ModelChoiceField(
        Device.objects.all(), label='デバイスID',
        widget=autocomplete.ModelSelect2(url='ptop:device_autocomplete'),
        help_text='デバイスIDを部分一致検索します。', required=True)
    errors = forms.ModelMultipleChoiceField(
        Error.objects.all(), label='エラーメッセージ',
        widget=autocomplete.ModelSelect2Multiple(url='ptop:error_autocomplete'),
        help_text='エラーメッセージを部分一致検索します。空白部をクリックまたはTab→キー入力で複数選択可能。',
        required=False)
    attachments = forms.ModelMultipleChoiceField(
        Attachment.objects.all(), label='添付ファイル', required=False)

#	def __init__(self, *args, **kwargs):
#		super(EventCreateForm, self).__init__(*args, **kwargs)
#		self.fields['operation_type'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data.get('start_time'))
        if cleaned_data.get('start_time') > cleaned_data.get('end_time'):
            print(cleaned_data.get('end_time'))
            raise forms.ValidationError("復旧日時は発生日時より後にしてください。")
        super().clean()

    class Meta:
        model = TroubleEvent
        fields = (
            'title', 'group', 'device',
            'description', 'trigger', 'cause', 'temporary_action', 'errors',
            'start_time', 'downtime', 'operation_type', 'end_time', 'delay_flag', 'delaytime',
            'input_operator', 'handling_operators', 'reported_physicist', 'attachments')

class GroupCreateForm(forms.ModelForm):
    device = forms.ModelChoiceField(
        label='デバイス', queryset=Device.objects, required=False,
        widget=SuggestWidget(attrs={'data-url': reverse_lazy('ptop:api_devices_get')}))
    is_common_trouble = forms.BooleanField(
        help_text='チェックするとトップページのよくあるトラブルに登録され、再発事象の入力が簡単になります',
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['path'].widget.attrs['readonly'] = 'readonly'

    class Meta:
        model = TroubleGroup
        fields = (
            'title', 'device', 'description', 'cause', 'causetype',
            'common_action', 'permanent_action', 'errors',
            'handling_status', 'vendor_status',
            'first_datetime', 'reminder_datetime', 'is_common_trouble',
            'criticality_score', 'frequency_score', 'difficulty_score',
            'path', 'classify_operator')

class ChangeOperationForm(forms.Form):
    operation_type = forms.ModelChoiceField(queryset=OperationType.objects.all(), label='次のオペレーション')
    change_time = forms.DateTimeField(initial=timezone.now, label='切り替え時刻')

    num_treat_hc1 = forms.IntegerField(initial=0, label='HC1治療ポート数')
    num_treat_gc2 = forms.IntegerField(initial=0, label='GC2治療ポート数')
    num_qa_hc1 = forms.IntegerField(initial=0, label='HC1 QAポート数')
    num_qa_gc2 = forms.IntegerField(initial=0, label='GC2 QAポート数')
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols':'60', 'rows':'4'}),
        label='コメント', required=False)
