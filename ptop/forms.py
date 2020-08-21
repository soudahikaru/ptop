from django import forms
from django.urls import reverse_lazy
from .models import TroubleEvent, Device, Error
from .models import TroubleGroup
from django.contrib.admin.widgets import FilteredSelectMultiple
from dal import autocomplete

from .widgets import SuggestWidget

class EventCreateForm(forms.ModelForm):
	device = forms.ModelChoiceField(Device.objects.all(), widget=autocomplete.ModelSelect2(url='ptop:device_autocomplete'))
	errors = forms.ModelMultipleChoiceField(Error.objects.all(), widget=autocomplete.ModelSelect2Multiple(url='ptop:error_autocomplete'))

	class Meta:
		model = TroubleEvent
		fields = ('title', 'device', 'description', 'cause', 'temporary_action', 'errors', 'start_time', 'end_time', 'downtime', 'delay_flag', 'delaytime', 'input_operator', 'handling_operators', 'reported_physicist')

class GroupCreateForm(forms.ModelForm):
	device = forms.ModelChoiceField(
		label='デバイス', queryset=Device.objects, required=False,
		widget=SuggestWidget(attrs={'data-url': reverse_lazy('ptop:api_devices_get')})
	)

	class Meta:
		model = TroubleGroup
		fields = ('title', 'device', 'description', 'cause')
