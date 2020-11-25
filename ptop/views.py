from datetime import datetime, date, timedelta
from django.shortcuts import render,redirect
from django.views.generic import ListView, DetailView, CreateView
from .forms import AttachmentForm
from .forms import EventCreateForm
from .forms import GroupCreateForm
from .forms import AdvancedSearchForm
from .models import Device, Error
from .models import TroubleEvent, TroubleGroup
from .models import Attachment
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404
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

		
class GroupDetailView(DetailView):
	template_name = 'group_detail.html'
	model = TroubleGroup

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		print(self.kwargs.get('pk'))
		context['events'] = TroubleEvent.objects.filter(group_id=self.kwargs.get('pk'))
#		print(events)
		return context

class EventDetailView(DetailView):
	template_name = 'event_detail.html'
	model = TroubleEvent

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

class RecurrentEventCreateFromEventView(CreateView):
	template_name = 'create_event.html'
	model = TroubleEvent
	form_class = EventCreateForm
	success_url = reverse_lazy('ptop:home')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		event = get_object_or_404(TroubleEvent, pk=self.kwargs.get('pk'))
		context['form'] = EventCreateForm( initial = { 
			'title':event.title,
			'group':event.group,
			'device':event.device,
			'description':event.description,
			'cause':event.cause,
			'temporary_action':event.temporary_action,
			'errors':[i.id for i in event.errors.all()],
			'start_time':timezone.now,
			'end_time':timezone.now,
			}
			)
		return context

class RecurrentEventCreateFromGroupView(CreateView):
	template_name = 'create_event.html'
	model = TroubleEvent
	form_class = EventCreateForm
	success_url = reverse_lazy('ptop:home')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
		context['form'] = EventCreateForm( initial = { 
			'title':group.title,
			'group':group,
			'device':group.device,
			'description':group.description,
			'cause':group.cause,
			'temporary_action':group.common_action,
			'errors':[i.id for i in group.errors.all()],
			'start_time':timezone.now,
			'end_time':timezone.now,
			}
			)
		return context
		
class EventCreateView(CreateView):
	template_name = 'create_event.html'
	model = TroubleEvent
	form_class = EventCreateForm
	success_url = reverse_lazy('ptop:home')
	attachment_files = []

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = EventCreateForm( initial = { 
			'start_time':timezone.now,
			'end_time':timezone.now,
			}
			)
		return context

	def post(self, request, *args, **kwargs):
		if self.request.FILES:
			print(self.request.FILES)
			form = AttachmentForm(self.request.POST, self.request.FILES)
			instance = self.get_form()
			form_data=instance.data.copy()
			print(form_data)
			print(instance.fields['attachments'])
			if form.is_valid():
				attachment_form = form.instance
				data = {'is_valid': True, 'name': attachment_form.file.name, 'url': attachment_form.file.url}
				print(attachment_form.file)
				attachment = Attachment.objects.create(title=attachment_form.file.name,file=attachment_form.file,description='',uploaded_datetime=datetime.now())
				print(attachment.pk)
				instance.attachments=[attachment]
				self.attachment_files.append(attachment) 
				print(instance.attachments)
			else:
				data = {'is_valid': False}
			return JsonResponse(data)
		else:
			context_object_name = 'sample_create'
			print(self.attachment_files)
			form = self.form_class(request.POST)
			obj =form.save(commit=False)
			print(form.cleaned_data['attachments'])
			if form.is_valid():
				if self.attachment_files:
					form.save()
					form.cleaned_data['attachments'].append(self.attachment_files)
					obj = form.save()
					print(obj)
				else:
					obj = form.save()
			print(obj)
			return redirect('ptop:event_detail',pk=obj.pk)


class AdvancedSearchView(ListView):
	template_name = 'advanced_search.html'
	searchForm = AdvancedSearchForm
	model = TroubleGroup

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# sessionに値がある場合、その値をセットする。（ページングしてもform値が変わらないように）
#		title = ''
#		text = ''
#		if 'form_value' in self.request.session:
#			form_value = self.request.session['form_value']
#			title = form_value[0]
#			text = form_value[1]
#		default_data = {'title': title,  # タイトル
#						'text': text,  # 内容
#						}
		if not self.request.GET.get('date_type'):
			date_type = '0'
		else:
			date_type = self.request.GET.get('date_type'),
		default_data = {
			'classify_id' : self.request.GET.get('classify_id'),
			'title' : self.request.GET.get('title'),
			'description' : self.request.GET.get('description'),
			'cause' : self.request.GET.get('cause'),
			'device' : self.request.GET.get('device'),
			'error' : self.request.GET.get('error'),
			'date_type' : date_type,
			'date_delta1' : self.request.GET.get('date_delta1'),
			'date2' : self.request.GET.get('date2'),
			'date_delta2' : self.request.GET.get('date_delta2'),
			'date3s' : self.request.GET.get('date3s'),
			'date3e' : self.request.GET.get('date3e'),
			'causetype' : self.request.GET.get('causetype'),
			'vendor_status' : self.request.GET.get('vendor_status'),
			'handling_status' : self.request.GET.get('handling_status'),
		}
		search_form = AdvancedSearchForm(initial=default_data) # 検索フォーム
		context['search_form'] = search_form
		return context
		
	def get_queryset(self):
		queryset = super().get_queryset()
#		print(queryset)
		form = self.search_form = AdvancedSearchForm(self.request.GET or None)
		if form.is_valid():
			classify_id = form.cleaned_data.get('classify_id')
			if classify_id:
				queryset = queryset.filter(Q(classify_id__exact=classify_id))
			title = form.cleaned_data.get('title')
			if title:
				queryset = queryset.filter(Q(title__icontains=title))
			description = form.cleaned_data.get('description')
			if description:
				queryset = queryset.filter(Q(description__icontains=description))
			device = form.cleaned_data.get('device')
			if device:
				queryset = queryset.filter(Q(device__device_id__icontains=device))
			error = form.cleaned_data.get('error')
			if error:
				queryset = queryset.filter(Q(errors__error_code__icontains=error))
			date_type = form.cleaned_data.get('date_type')
			print (date_type)
			if date_type=='1':
				date_delta1 = int(form.cleaned_data.get('date_delta1'))
				print(date_delta1)
				print((datetime.now()-timedelta(days=date_delta1),datetime.now))
				queryset = queryset.filter(Q(first_datetime__range=(datetime.now()-timedelta(days=date_delta1),datetime.now())))
			elif date_type=='2':
				date2 = form.cleaned_data.get('date2')
				date_delta2 = int(form.cleaned_data.get('date_delta2'))
				queryset = queryset.filter(Q(first_datetime__range=(date2-timedelta(days=date_delta2),date2+timedelta(days=date_delta2))))
			elif date_type=='3':
				date3s = form.cleaned_data.get('date3s')
				date3e = form.cleaned_data.get('date3e')
				queryset = queryset.filter(Q(first_datetime__range=(date3s,date3e)))
			causetype = form.cleaned_data.get('causetype')
			if not causetype=='NOSELECT':
				queryset = queryset.filter(Q(causetype=causetype))
			vendor_status = form.cleaned_data.get('vendor_status')
			if not vendor_status=='NOSELECT':
				queryset = queryset.filter(Q(vendor_status=vendor_status))
			handling_status = form.cleaned_data.get('handling_status')
			if not handling_status=='NOSELECT':
				queryset = queryset.filter(Q(handling_status=handling_status))
		object_list = queryset
		return object_list


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

