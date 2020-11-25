from django import forms
from django.urls import reverse_lazy
from .models import TroubleEvent, Device, Error
from .models import TroubleGroup
from .models import Attachment
from django.contrib.admin.widgets import FilteredSelectMultiple
import bootstrap_datepicker_plus as datetimepicker
from dal import autocomplete
from django.core import validators

from .widgets import SuggestWidget

class AttachmentForm(forms.ModelForm):
	class Meta:
		model = Attachment
		fields = ('file',)


class AdvancedSearchForm(forms.Form):
	CHOICE = (
		('0',''),
		('1',''),
		('2',''),
		('3',''),
	)
	tuple_noselect = (('NOSELECT','指定しない'),)
	classify_id = forms.CharField(label='分類ID', max_length=100,required=False)
	title = forms.CharField(label='題名', max_length=100,required=False)
	description = forms.CharField(label='内容', max_length=100,required=False)
	cause = forms.CharField(label='原因', max_length=100,required=False)
	error = forms.CharField(label='エラーメッセージ', max_length=100,required=False)
	device = forms.CharField(label='デバイスID', max_length=100,required=False)
	date_type = forms.ChoiceField(label='', widget=forms.RadioSelect, choices=CHOICE, initial='0')
	date_delta1 = forms.IntegerField(widget=forms.NumberInput(attrs={'style': 'width:6ch',}),validators=[validators.MinValueValidator(0)],required=False)
	date2 = forms.DateField(widget=datetimepicker.DatePickerInput(format='%Y-%m-%d',options={'locale': 'ja','dayViewHeaderFormat': 'YYYY年 MMMM',}),required=False)
	date_delta2 = forms.IntegerField(widget=forms.NumberInput(attrs={'style': 'width:6ch',}),validators=[validators.MinValueValidator(0)],required=False)
	date3s = forms.DateField(widget=datetimepicker.DatePickerInput(format='%Y-%m-%d',options={'locale': 'ja','dayViewHeaderFormat': 'YYYY年 MMMM',}).start_of('期間'),required=False)
	date3e = forms.DateField(widget=datetimepicker.DatePickerInput(format='%Y-%m-%d',options={'locale': 'ja','dayViewHeaderFormat': 'YYYY年 MMMM',}).end_of('期間'),required=False)
#	print(tuple_noselect+TroubleGroup.VENDOR_STATUS)
	causetype = forms.ChoiceField(label='原因類型', choices=tuple_noselect+TroubleGroup.CAUSETYPES,required=False)
	vendor_status = forms.ChoiceField(label='メーカー対応状況', choices=tuple_noselect+TroubleGroup.VENDOR_STATUS,required=False)
	handling_status = forms.ChoiceField(label='対処状況', choices=tuple_noselect+TroubleGroup.HANDLING_STATUS,required=False)

class EventCreateForm(forms.ModelForm):
	device = forms.ModelChoiceField(Device.objects.all(), label='デバイスID', widget=autocomplete.ModelSelect2(url='ptop:device_autocomplete'),help_text='デバイスIDを部分一致検索します。')
	errors = forms.ModelMultipleChoiceField(Error.objects.all(), label='エラーメッセージ', widget=autocomplete.ModelSelect2Multiple(url='ptop:error_autocomplete'),help_text='エラーメッセージを部分一致検索します。空白部をクリックまたはTab→キー入力で複数選択可能。')
	attachments = forms.ModelMultipleChoiceField(Attachment.objects.all(), label='添付ファイル')

	class Meta:
		model = TroubleEvent
		fields = ('title', 'group', 'device', 'description', 'cause', 'temporary_action', 'errors', 'start_time', 'end_time', 'downtime', 'delay_flag', 'delaytime', 'input_operator', 'handling_operators', 'reported_physicist', 'attachments')
		widgets={
			'title':forms.TextInput(attrs={'size':80}),
			'description':forms.Textarea(attrs={'rows':4, 'cols':80}),
			'cause':forms.Textarea(attrs={'rows':4, 'cols':80}),
			'temporary_action':forms.Textarea(attrs={'rows':4, 'cols':80}),
		}

class GroupCreateForm(forms.ModelForm):
	device = forms.ModelChoiceField(
		label='デバイス', queryset=Device.objects, required=False,
		widget=SuggestWidget(attrs={'data-url': reverse_lazy('ptop:api_devices_get')})
	)
	is_common_trouble = forms.BooleanField(help_text='チェックするとトップページのよくあるトラブルに登録され、再発事象の入力が簡単になります', required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['path'].widget.attrs['readonly'] = 'readonly'

	class Meta:
		model = TroubleGroup
		fields = ('title', 'device', 'description', 'cause', 'causetype', 'common_action','permanent_action', 'errors','handling_status','vendor_status', 'first_datetime', 'reminder_datetime', 'is_common_trouble','criticality_score', 'frequency_score', 'difficulty_score', 'path', 'classify_operator')
