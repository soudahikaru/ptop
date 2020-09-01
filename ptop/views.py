from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView
from .forms import EventCreateForm
from .forms import GroupCreateForm
from .models import Device, Error
from .models import TroubleEvent, TroubleGroup
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from dal import autocomplete

# Create your views here.

def api_devices_get(request):
	"""サジェスト候補のデバイスIDをJSONで返す。"""
	keyword = request.GET.get('keyword')
	if keyword:
		post_list = [{'pk': item.pk, 'name': item.device_id} for item in Device.objects.filter(device_id__icontains=keyword)]
	else:
		post_list = []
	return JsonResponse({'object_list': post_list})

class DeviceAutoComplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		qs = Device.objects.all()
		if self.q:
			qs = qs.filter(device_id__icontains=self.q)
		return qs

class ErrorAutoComplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		qs = Error.objects.all()
		if self.q:
			qs = qs.filter(error_code__icontains=self.q)
		return qs

class TroubleEventDetail(DetailView):
	template_name = 'event.html'
	model = TroubleEvent
	
class TroubleEventList(ListView):
	template_name = 'eventlist.html'
	model = TroubleEvent

	def get_queryset(self):
		q_word = self.request.GET.get('query')
		if q_word:
			object_list = TroubleEvent.objects.filter(
			Q(title__icontains=q_word) | Q(description__icontains=q_word))
		else:
			object_list = TroubleEvent.objects.all()
		return object_list	
	
class GroupCreateFromEventView(CreateView):
	template_name = 'group_create.html'
	model = TroubleGroup
	form_class = GroupCreateForm
	success_url = reverse_lazy('ptop:home')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		event = get_object_or_404(TroubleEvent, pk=self.kwargs.get('pk'))
		context['form'] = GroupCreateForm( initial = { 
			'title':event.title,
			'device':event.device,
			'description':event.description,
			'cause':event.cause,
			'first_datetime':event.start_time,
			'common_action':event.temporary_action}
			 )
		return context

class ChildGroupCreateView(CreateView):
	template_name = 'group_create.html'
	model = TroubleGroup
	form_class = GroupCreateForm
	success_url = reverse_lazy('ptop:home')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		parent_group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
		context['form'] = GroupCreateForm( initial = { 
			'title':parent_group.title + '(sub)',
			'description':parent_group.description,
			'cause':parent_group.cause,
			'common_action':parent_group.common_action,
			'path':parent_group.path}
			 )
		return context
		
class EventCreateView(CreateView):
	template_name = 'create_event.html'
	model = TroubleEvent
	form_class = EventCreateForm
	success_url = reverse_lazy('ptop:home')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = EventCreateForm( initial = { 
			'start_time':timezone.now,
			'end_time':timezone.now,
			}
			)
		return context

class EventClassifyView(ListView):
	template_name = 'event_classify.html'
	model = TroubleEvent

def event_classify(request, pk):
	event = TroubleEvent.objects.get(pk=pk)
	q_word = request.GET.get('query')
	if q_word:
		object_list = TroubleGroup.objects.filter(
		Q(title__icontains=q_word) | Q(description__icontains=q_word) | Q(device__name__icontains=q_word))
	else:
		object_list = TroubleGroup.objects.all()

	group_pk = request.GET.get('selected_group')
	if group_pk:
		group = TroubleGroup.objects.get(pk=group_pk)
	else:
		group = None

	return render(request, 'event_classify.html', {'event':event,'object_list':object_list,'group':group})

def event_classify_execute(request):
	event_pk = request.GET.get('event_pk')
	group_pk = request.GET.get('group_pk')
	event = TroubleEvent.objects.get(pk=event_pk)
	if group_pk!='None':
		group = TroubleGroup.objects.get(pk=group_pk)
	else:
		group = None
	event.group = group
	event.save()
	return HttpResponseRedirect("/unapproved_event_list/")

class UnapprovedEventListView(ListView):
	model = TroubleEvent
	template_name = "unapproved_event_list.html"
	def get_queryset(self):
		object_list = TroubleEvent.objects.filter(Q(approval_operator=None))
		return object_list

	def sample(request):
		loggedin_userid = request.user.id

	def post(self, request, *args, **kwargs):
		update_object_list = TroubleEvent.objects.filter(Q(approval_operator=None)&~Q(group=None))
		if request.user.groups.filter(name='Operator').exists():
			for item in update_object_list:
				print(item.title)
				item.approval_operator = request.user
				item.save()
		return render(request, 'unapproved_event_list.html')
		
class Home(ListView):
	template_name = 'home.html'
	model = TroubleEvent

	def get_queryset(self):
		object_list = TroubleEvent.objects.order_by('start_time').reverse()[:5]
		return object_list

