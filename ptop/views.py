""" PTOP view module """

import pytz
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils import timezone
#from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.db.models import IntegerField, DurationField, FloatField
from django.db.models import Sum, F, Func, Count, ExpressionWrapper
from django.db.models.functions import Cast, TruncDay, TruncMonth, TruncYear, Trunc, Extract
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_pandas.io import read_frame
import pandas as pd
import numpy as np
#from django.shortcuts import get_list_or_404
from dal import autocomplete
from .forms import AttachmentForm
from .forms import EventCreateForm
from .forms import GroupCreateForm
from .forms import AdvancedSearchForm
from .forms import EventAdvancedSearchForm
from .forms import ChangeOperationForm
from .forms import OperationCreateForm
from .forms import StatisticsForm
from .forms import AnnouncementCreateForm
from .models import Device, Error
from .models import TroubleEvent, TroubleGroup
from .models import Attachment
from .models import Operation
from .models import Announcement

# Create your views here.

def api_devices_get(request):
    """（不使用）サジェスト候補のデバイスIDをJSONで返す。"""
    keyword = request.GET.get('keyword')
    if keyword:
        post_list = [
            {'pk': item.pk, 'name': item.device_id} for item in Device.objects.filter(
                device_id__icontains=keyword)
            ]
    else:
        post_list = []
    return JsonResponse({'object_list': post_list})

def ajax_search_operation_from_datetime(request):
    """OperationTypeのIDをJSONで返す関数。"""
    if request.is_ajax and request.method == "GET":
        time = request.GET.get("time", None)
        print(time)
        if time:
            ope = Operation.objects.filter(end_time__gte=time).first()
            if not ope:
                print('newest operation')
                ope = Operation.objects.order_by('start_time').last()
            print(ope.operation_type.id)
            return JsonResponse({'operation_type':ope.operation_type.id})
        else:
            return JsonResponse({'operation_type':None})
    else:
        return JsonResponse({})

class DeviceAutoComplete(autocomplete.Select2QuerySetView):
    """Deviceを部分一致検索して入力"""
    def get_queryset(self):
        qs = Device.objects.all()
        if self.q:
            qs = qs.filter(Q(device_id__icontains=self.q) | Q(name__icontains=self.q))
        return qs

    def get_result_label(self, item):
        return '%s(%s)' % (item.device_id, item.name)

class ErrorAutoComplete(autocomplete.Select2QuerySetView):
    """Errorを部分一致検索して入力"""
    def get_queryset(self):
        qs = Error.objects.all()
        if self.q:
            qs = qs.filter(error_code__icontains=self.q)
        return qs

class TroubleGroupListView(ListView):
    """TroubleGroupList画面"""
    template_name = 'group_list.html'
    model = TroubleGroup
    paginate_by = 10

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = TroubleGroup.objects.filter(
                Q(title__icontains=q_word) | Q(description__icontains=q_word)
            )
        else:
            object_list = TroubleGroup.objects.all().order_by('id').reverse()
        return object_list

class DeviceCreate(CreateView):
    """新規Deviceの作成"""
    model = Device
    template_name = 'device_form.html'
    fields = '__all__'
    success_url = reverse_lazy('ptop:home')

class PopupDeviceCreate(DeviceCreate):
    """ポップアップでのDevice作成"""

    def form_valid(self, form):
        device = form.save()
        context = {
            'object_name': device.device_id,
            'object_pk': device.pk,
            'function_name': 'add_device'
        }
        return render(self.request, 'close.html', context)

class ErrorCreate(CreateView):
    """新規Errorの作成"""
    model = Error
    template_name = 'error_form.html'
    fields = '__all__'
    success_url = reverse_lazy('ptop:home')

class PopupErrorCreate(ErrorCreate):
    """ポップアップでのError作成"""

    def form_valid(self, form):
        error = form.save()
        context = {
            'object_name': error.error_code,
            'object_pk': error.pk,
            'function_name': 'add_error'
        }
        return render(self.request, 'close.html', context)

class GroupDetailView(DetailView):
    """TroubleGroup詳細画面"""
    template_name = 'group_detail.html'
    model = TroubleGroup

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
#        context['events'] = TroubleEvent.objects.filter(group_id=self.kwargs.get('pk'))
        startpath = '/' + context.get('object').path.split('/')[1] + '/'
        print(startpath)
        context['events'] = TroubleEvent.objects.filter(group__path__startswith=startpath)
        context['child_group'] = TroubleGroup.objects.filter(path__startswith=startpath)
#		print(events)
        return context

class EventDetailView(DetailView):
    """TroubleEvent詳細画面"""
    template_name = 'event_detail.html'
    model = TroubleEvent

class TroubleEventDetail(DetailView):
    """TroubleEvent詳細画面(旧ver)"""
    template_name = 'event.html'
    model = TroubleEvent

class TroubleEventList(ListView):
    """TroubleEventList画面"""
    template_name = 'eventlist.html'
    model = TroubleEvent
    paginate_by = 10

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = TroubleEvent.objects.filter(
                Q(title__icontains=q_word) | Q(description__icontains=q_word)
            ).order_by('start_time').reverse()
        else:
            object_list = TroubleEvent.objects.all().order_by('start_time').reverse()
        return object_list

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('query', '')
        return ctx

class GroupBaseMixin(LoginRequiredMixin, object):
    """各種Group作成/更新画面のベースとなる処理"""
    template_name = 'create_group.html'
    model = TroubleGroup
    form_class = GroupCreateForm

#    def get_object(self, queryset=None):
#    # get the existing object or created a new one
#        obj, created = TroubleGroup.objects.get_or_create(pk=self.kwargs['pk'])
#        print(obj)
#        return obj

    def get_success_url(self):
        return reverse_lazy('ptop:group_detail', kwargs={'pk': self.object.id})
#    success_url = reverse_lazy('ptop:eventlist')

    def post(self, request, *args, **kwargs):
        if self.request.FILES:
            print(self.request.FILES)
            form = AttachmentForm(self.request.POST, self.request.FILES)
            if form.is_valid():
                attachment_form = form.instance
                attachment = Attachment.objects.create(
                    title=attachment_form.file.name,
                    file=attachment_form.file,
                    description='',
                    uploaded_datetime=datetime.now()
                    )
                data = {
                    'is_valid': True,
                    'pk': attachment.pk,
                    'title': attachment.title,
                    }
                print(data)
            else:
                data = {'is_valid': False}
            return JsonResponse(data)
        elif 'from_event' in self.request.path:
            event_pk = self.kwargs.get('pk')
            print('event_pk=', event_pk)
            if event_pk:
                event = TroubleEvent.objects.get(pk=event_pk)
                print(event)
                form = self.form_class(request.POST)
                if form.is_valid():
                    obj = form.save()
                    event.group = obj
                    print('group_pk=', obj.pk)
                    print('event.group', event.group)
                    event.save()
#            return redirect('ptop:group_detail', pk=obj.pk)
            return redirect('ptop:unapproved_event_list')
            
        else:
            return super().post(request, *args, **kwargs)
#            form = self.form_class(request.POST)
#            if form.is_valid():
#                obj = form.save(commit=False)
#                print(obj)
#                obj.save()
#                return redirect('ptop:group_detail', pk=self.kwargs['pk'])
#            else:
#                return render(request, 'create_group.html', {'form': form})

class EventBaseMixin(LoginRequiredMixin, object):
    """各種Event作成/更新画面のベースとなる処理"""
    template_name = 'create_event.html'
    model = TroubleEvent
    form_class = EventCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:event_detail', kwargs={'pk': self.object.id})

    def post(self, request, *args, **kwargs):
        if self.request.FILES:
            print(self.request.FILES)
            form = AttachmentForm(self.request.POST, self.request.FILES)
            if form.is_valid():
                attachment_form = form.instance
                attachment = Attachment.objects.create(
                    title=attachment_form.file.name,
                    file=attachment_form.file,
                    description='',
                    uploaded_datetime=datetime.now()
                    )
                data = {
                    'is_valid': True,
                    'pk': attachment.pk,
                    'title': attachment.title,
                    }
                print(data)
            else:
                data = {'is_valid': False}
            return JsonResponse(data)
        else:
#            form = EventCreateForm(self.request.POST)
#            form.fields['attachments'].queryset = Attachment.objects.all().order_by('id')
#            print(self.request.POST)
#            print(form.fields['attachments'].queryset.reverse())
            return super().post(request, *args, **kwargs)

class GroupCreateFromEventView(GroupBaseMixin, CreateView):
    """Event情報から新しいGroupを作る画面"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(TroubleEvent, pk=self.kwargs.get('pk'))
        context['base_event'] = self.kwargs.get('pk')
        context['form'] = GroupCreateForm(initial={
            'title':event.title,
            'device':event.device,
            'description':event.description,
            'cause':event.cause,
            'first_datetime':event.start_time,
            'common_action':event.temporary_action,
            'classify_operator':self.request.user,
        })
        return context

class ChildGroupCreateView(GroupBaseMixin, CreateView):
    """あるGroupから子Groupを作る画面"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
        context['form'] = GroupCreateForm(initial={
            'title':parent_group.title + '(sub)',
            'description':parent_group.description,
            'cause':parent_group.cause,
            'common_action':parent_group.common_action,
            'path':parent_group.path,
            'classify_operator':self.request.user,
            })
        return context

class RecurrentEventCreateFromEventView(EventBaseMixin, CreateView):
    """Eventから再発Eventを入力する画面"""
    template_name = 'create_event.html'
    model = TroubleEvent
    form_class = EventCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(TroubleEvent, pk=self.kwargs.get('pk'))
        context['form'] = EventCreateForm(initial={
            'title':event.title,
            'group':event.group,
            'device':event.device,
            'description':event.description,
            'cause':event.cause,
            'temporary_action':event.temporary_action,
            'errors':[i.id for i in event.errors.all()],
            'start_time':timezone.now,
            'end_time':timezone.now,
            })
        return context

class RecurrentEventCreateFromGroupView(CreateView):
    """Groupから再発Eventを入力する画面"""
    template_name = 'create_event.html'
    model = TroubleEvent
    form_class = EventCreateForm
    success_url = reverse_lazy('ptop:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
        context['form'] = EventCreateForm(initial={
            'title':group.title,
            'group':group,
            'device':group.device,
            'description':group.description,
            'cause':group.cause,
            'temporary_action':group.common_action,
            'errors':[i.id for i in group.errors.all()],
            })
        return context

class EventCreateView(EventBaseMixin, CreateView):
    """Event新規入力画面"""
    template_name = 'create_event.html'
    model = TroubleEvent
    form_class = EventCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EventCreateForm(initial={
            'input_operator':self.request.user,
            })
        return context


class EventUpdateView(EventBaseMixin, UpdateView):
    """Event編集画面"""
    model = TroubleEvent
    form_class = EventCreateForm
    template_name = 'create_event.html'

class GroupUpdateView(GroupBaseMixin, UpdateView):
    """Group編集画面"""
    model = TroubleGroup
    form_class = GroupCreateForm
    template_name = 'create_group.html'

    def get_success_url(self):
        return reverse_lazy('ptop:group_detail', kwargs={'pk': self.object.id})
#    success_url = reverse_lazy('ptop:eventlist')

class AdvancedSearchView(ListView):
    """Group詳細検索画面"""
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

class EventAdvancedSearchView(ListView):
    """Event詳細検索画面"""
    template_name = 'event_advanced_search.html'
    searchForm = EventAdvancedSearchForm
    model = TroubleEvent
    
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
            'id' : self.request.GET.get('id'),
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
            'downtime_low' : self.request.GET.get('downtime_low'),
            'downtime_high' : self.request.GET.get('downtime_high'),
            'delaytime_low' : self.request.GET.get('delaytime_low'),
            'delaytime_high' : self.request.GET.get('delaytime_high'),
        }
        search_form = EventAdvancedSearchForm(initial=default_data) # 検索フォーム
        context['search_form'] = search_form
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
#		print(queryset)
        form = self.search_form = EventAdvancedSearchForm(self.request.GET or None)
        if form.is_valid():
            id = form.cleaned_data.get('id')
            if id:
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
            print(date_type)
            if date_type == '1':
                date_delta1 = int(form.cleaned_data.get('date_delta1'))
                print(date_delta1)
                print((datetime.now() - timedelta(days=date_delta1), datetime.now))
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            datetime.now() - timedelta(days=date_delta1),
                            datetime.now()
                        )
                    )
                )
            elif date_type == '2':
                date2 = form.cleaned_data.get('date2')
                date_delta2 = int(form.cleaned_data.get('date_delta2'))
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            date2-timedelta(days=date_delta2),
                            date2+timedelta(days=date_delta2)
                        )
                    )
                )
            elif date_type == '3':
                date3s = form.cleaned_data.get('date3s')
                date3e = form.cleaned_data.get('date3e')
                queryset = queryset.filter(Q(start_time__range=(date3s, date3e)))
            print(form.cleaned_data)
            if form.cleaned_data.get('downtime_low'):
                print(form.cleaned_data.get('downtime_low'))
                queryset = queryset.filter(Q(downtime__gte=int(form.cleaned_data.get('downtime_low'))))
            if form.cleaned_data.get('downtime_high'):
                print(form.cleaned_data.get('downtime_high'))
                queryset = queryset.filter(Q(downtime__lte=int(form.cleaned_data.get('downtime_high'))))
            if form.cleaned_data.get('delaytime_low'):
                queryset = queryset.filter(Q(delaytime__gte=int(form.cleaned_data.get('delaytime_low'))))
            if form.cleaned_data.get('delaytime_high'):
                queryset = queryset.filter(Q(delaytime__lte=int(form.cleaned_data.get('delaytime_high'))))
        object_list = queryset
        return object_list

class OperationListView(ListView):
    """OperationList画面"""
    template_name = 'operation_list.html'
    model = Operation
    paginate_by = 10

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = Operation.objects.filter(
                Q(start_time__date=datetime.strptime(q_word, '%Y/%m/%d'))
            ).order_by('start_time').reverse()
        else:
            object_list = Operation.objects.all().order_by('start_time').reverse()
        return object_list


class OperationBaseMixin(LoginRequiredMixin, object):
    """Operationの作成/編集ベース"""
    template_name = 'create_operation.html'
    model = Operation
    success_url = reverse_lazy('ptop:operation_list')

    def post(self, request, *args, **kwargs):
        start = request.POST['start_time']
        end = request.POST['end_time']
        # 1: 既存のOperationの範囲がstart_timeをまたいでいる場合(完全に既存のOpに含まれる場合もここでひっかかる)
        # 2: 既存のOperationの範囲がend_timeをまたいでいる場合
        # かつ、そのOperationが自分自身でなく、装置停止でもない場合
        # には作成を受け付けない
        print(kwargs.get('pk'))
        query_set = Operation.objects.filter(
            ~Q(id__exact=kwargs.get('pk')) 
                & ~Q(operation_type__name__exact='装置停止')
                & ((Q(start_time__lt=start) & Q(end_time__gt=start))
                    |(Q(start_time__lt=end) & Q(end_time__gt=end)))
            )
        if query_set.first():
            print(query_set)
            return render(
                request,
                'create_operation.html',
                {'form': OperationCreateForm(request.POST), 'overlapped_oparations':query_set}
                )
        return super().post(request, *args, **kwargs)

class OperationUpdateView(OperationBaseMixin, UpdateView):
    """過去のOperationの編集"""
    template_name = 'create_operation.html'
    model = Operation
    form_class = OperationCreateForm

class OperationCreateView(OperationBaseMixin, CreateView):
    """過去のOperationの作成"""
    template_name = 'create_operation.html'
    model = Operation
    form_class = OperationCreateForm

@login_required
def change_operation(request):
    """Operation変更画面"""
    current_operation = Operation.objects.order_by('start_time').last()
    if current_operation:
        return render(
            request,
            'change_operation.html',
            {'current_operation':current_operation, 'change_form':ChangeOperationForm}
            )
    else:
        return render(
            request,
            'change_operation.html',
            {'current_operation':None, 'change_form':ChangeOperationForm}
            )

def change_operation_execute(request):
    """Operation変更実行"""
    form = ChangeOperationForm(data=request.POST)
    form.full_clean()
    current_operation = Operation.objects.order_by('start_time').last()
    if current_operation:
        current_operation.end_time = form.cleaned_data.get('change_time')
        current_operation.operation_time = (current_operation.end_time - current_operation.start_time).total_seconds() / 60.0
        current_operation.save()
        new_operation = Operation.objects.create(
            operation_type=form.cleaned_data.get('operation_type'),
            start_time=form.cleaned_data.get('change_time'),
            num_treat_hc1=form.cleaned_data.get('num_treat_hc1'),
            num_treat_gc2=form.cleaned_data.get('num_treat_gc2'),
            num_qa_hc1=form.cleaned_data.get('num_qa_hc1'),
            num_qa_gc2=form.cleaned_data.get('num_qa_gc2'),
            )
    else:
        current_operation = Operation.objects.create(
            operation_type=form.cleaned_data.get('operation_type'),
            start_time=form.cleaned_data.get('change_time'),
            )
    return HttpResponseRedirect("/change_operation/")

class AnnouncementListView(ListView):
    """AnnouncementList画面"""
    template_name = 'announcement_list.html'
    model = Announcement
    paginate_by = 10

    def get_queryset(self):
        return Announcement.objects.all().order_by('posted_time')

class AnnouncementDetailView(DetailView):
    """Announcement詳細画面"""
    template_name = 'announcement_detail.html'
    model = Announcement

class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Announcement作成画面"""
    template_name = 'announcement_create.html'
    model = Announcement
    form_class = AnnouncementCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:announcement_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AnnouncementCreateForm(initial={
            'user':self.request.user,
            })
        return context


class EventClassifyView(LoginRequiredMixin, ListView):
    """イベント分類View"""
    template_name = 'event_classify.html'
    model = TroubleEvent

@login_required
def event_classify(request, pk_):
    """イベント分類画面"""
    event = TroubleEvent.objects.get(pk=pk_)
    q_word = request.GET.get('query')
    if q_word:
        object_list = TroubleGroup.objects.filter(
            Q(title__icontains=q_word)
            | Q(description__icontains=q_word)
            | Q(device__name__icontains=q_word)
            )
    else:
        object_list = TroubleGroup.objects.all()

    group_pk = request.GET.get('selected_group')
    if group_pk:
        group = TroubleGroup.objects.get(pk=group_pk)
    else:
        group = None
    return render(
        request,
        'event_classify.html',
        {'event':event, 'object_list':object_list, 'group':group}
        )

def event_classify_execute(request):
    """イベント分類実行"""
    event_pk = request.GET.get('event_pk')
    group_pk = request.GET.get('group_pk')
    event = TroubleEvent.objects.get(pk=event_pk)
    if group_pk != 'None':
        group = TroubleGroup.objects.get(pk=group_pk)
    else:
        group = None
    event.group = group
    event.save()
    return HttpResponseRedirect("/unapproved_event_list/")

def make_dataframe(query_set, start_datetime, end_datetime, interval='day'):
    print(start_datetime, end_datetime)
    df = read_frame(query_set, index_col='index')
    print(df)
    tz_jp = pytz.timezone('Asia/Tokyo')
    freq_str = 'D'
    start_datetime_trunc = start_datetime
    end_datetime_trunc = end_datetime
    if interval == 'week':
        freq_str = 'W'
        return df
    elif interval == 'month':
        freq_str = 'M'
        start_datetime_trunc = tz_jp.localize(datetime(start_datetime.year, start_datetime.month, 1))
        end_datetime_trunc = tz_jp.localize(datetime(end_datetime.year, end_datetime.month, 1))
        return df
    elif interval == 'year':
        freq_str = 'Y'
        return df
    if not query_set.exists():
        s = pd.Series([0]*len(df.columns), index=df.columns, name=start_datetime)
        df = df.append(s)
        s = pd.Series([0]*len(df.columns), index=df.columns, name=end_datetime)
        df = df.append(s)
    else:
        first_index = df.index.array[0]
        last_index = df.index.array[-1]
        print("test")
        if  first_index != start_datetime_trunc:
            s = pd.Series([0]*len(df.columns), index=df.columns, name=start_datetime_trunc)
            df = df.append(s)
        if last_index != end_datetime_trunc:
            s = pd.Series([0]*len(df.columns), index=df.columns, name=end_datetime_trunc)
            df = df.append(s)
    print(df)
#    df = df.sort_index().asfreq(freq_str, fill_value=0).fillna(0)
    df = df.sort_index().asfreq(freq_str, fill_value=0).fillna(0)
    print(df)
    return df

def statistics_create_view(request):
    form = StatisticsForm()

    if request.method == 'POST':
        form = StatisticsForm(data=request.POST)
#        print(request.POST.get('df'))
        start = request.POST['date_s']
        end = request.POST['date_e']
        start_t = datetime.strptime(start, '%Y-%m-%d')
        end_t = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
        subtotal_frequency = request.POST['subtotal_frequency']
        if start and end:
            events = TroubleEvent.objects.filter(
                Q(start_time__gt=start_t) & Q(end_time__lt=end_t)
                ).order_by('start_time')
            operations = Operation.objects.filter(
                ~Q(operation_type__name__iexact='装置停止')
                & Q(start_time__gt=start_t) & Q(end_time__lt=end_t)
            ).order_by('start_time')
        else:
            events = TroubleGroup.objects.all()
            operations = Operation.objects.all()

        tz_jp = pytz.timezone('Asia/Tokyo')
        start_datetime = timezone.datetime.strptime(start, '%Y-%m-%d')
        start_localized = tz_jp.localize(start_datetime)
        end_datetime = timezone.datetime.strptime(end, '%Y-%m-%d')
        end_localized = tz_jp.localize(end_datetime)
        # troubleevent
        statistics_event = events.annotate(index=Trunc('start_time', kind=subtotal_frequency)) \
            .values('index') \
            .annotate(num_event=Count('id')) \
            .annotate(subtotal_downtime=Sum('downtime')) \
            .annotate(subtotal_delaytime=Sum('delaytime')) \
            .order_by('index')
        df_event = make_dataframe(statistics_event, start_localized, end_localized, subtotal_frequency)

        #operation
        statistics_operation = operations.annotate(index=Trunc('start_time', kind=subtotal_frequency)) \
            .values('index') \
            .annotate(subtotal_operation_time=Sum('operation_time')) \
            .annotate(subtotal_treatment_time=Sum('operation_time', filter=Q(operation_type__name__iexact='治療'))) \
            .order_by('index')
        df_operation = make_dataframe(statistics_operation, start_localized, end_localized, subtotal_frequency)

        df = pd.merge(df_operation, df_event, left_index=True, right_index=True, how='outer').fillna(0)
#        df['subtotal_operation_time'] = df['subtotal_operation_time'] / 60000000
#        df['subtotal_treatment_time'] = df['subtotal_treatment_time'] / 60000000
        s_summary = df.sum()
        s_summary.name = '合計'
        print(s_summary)
        df = df.append(s_summary)

        df['total_availability'] = 1.0 - (df['subtotal_downtime'].divide(df['subtotal_operation_time']))
        df['treatment_availability'] = 1.0 - (df['subtotal_delaytime'].divide(df['subtotal_treatment_time']))
#        print(df['subtotal_operation_time'])
#        df['operation_time_minute'] = df['subtotal_operation_time'].dt.total_seconds()
#        print(df)
  #      total_downtime = events.aggregate(value=Sum('downtime'))
 #       operations_annotate = operations.annotate(time_diff=(ExpressionWrapper(F('end_time')-F('start_time'), output_field=DurationField())))
        #print(operations_annotate)
#        total_operation_time = operations_annotate.aggregate(value=Sum('operation_time'))
#        s_summary['total_availability'] = 1.0 - (s_summary['subtotal_downtime'].divide(s_summary['subtotal_operation_time']))
#        s_summary['treatment_availability'] = 1.0 - (s_summary['subtotal_delaytime'].divide(s_summary['subtotal_treatment_time']))
        print(df)
        if request.POST.get('next', '') == 'CSV出力':
            response = HttpResponse(content_type='text/csv; charset=cp932')
            filename = 'stat%s.csv' % (datetime.today().strftime('%Y%m%d-%H%M'))
            print(filename)
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
            df.to_csv(path_or_buf=response, encoding='utf_8_sig')
            print(response)
            return response
        else:    
            return render(
                request,
                'statistics_create.html',
                {
                    'form':form, 
                    'subtotal_frequency':subtotal_frequency,
                    'df':df,
                    's_summary':s_summary,
                }
                )
    else:
        total_downtime = None
        total_operation_time = None
        total_availability = None
        return render(
            request,
            'statistics_create.html',
            {
                'form':form, 
                'total_downtime':0, 
                'total_operation_time':0,
                'total_availability':0.0,
            }
            )



class UnapprovedEventListView(ListView):
    """未承認イベント一覧画面"""
    model = TroubleEvent
    template_name = "unapproved_event_list.html"
    def get_queryset(self):
        object_list = TroubleEvent.objects.filter(Q(approval_operator=None))
        return object_list

    def sample(self, request):
        """sample function"""
        loggedin_userid = request.user.id

    def post(self, request, *args, **kwargs):
        """post時に呼ばれる関数"""
        update_object_list = TroubleEvent.objects.filter(Q(approval_operator=None)&~Q(group=None))
        if request.user.groups.filter(name='Operator').exists():
            for item in update_object_list:
                print(item.title)
                item.approval_operator = request.user
                item.save()
        return render(request, 'unapproved_event_list.html')

class Home(ListView):
    """ホーム画面"""
    template_name = 'home.html'
    model = TroubleEvent

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_operation'] = Operation.objects.order_by('start_time').last()
        context['announce_list'] = Announcement.objects.order_by('posted_time').reverse()[:5]
#        print(context)
        return context

    def get_queryset(self):
        object_list = TroubleEvent.objects.order_by('start_time').reverse()[:5]
#	return render(request, 'home.html', {'current_operation':current_operation})
        return object_list
