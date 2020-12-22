""" PTOP view module """

from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils import timezone
#from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
#from django.shortcuts import get_list_or_404
from dal import autocomplete
from .forms import AttachmentForm
from .forms import EventCreateForm
from .forms import GroupCreateForm
from .forms import AdvancedSearchForm
from .forms import ChangeOperationForm
from .models import Device, Error
from .models import TroubleEvent, TroubleGroup
from .models import Attachment
from .models import Operation

# Create your views here.

def api_devices_get(request):
    """サジェスト候補のデバイスIDをJSONで返す。"""
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
                ope = Operation.objects.order_by('id').last()
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
            qs = qs.filter(device_id__icontains=self.q)
        return qs

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
        print(self.kwargs.get('pk'))
        context['events'] = TroubleEvent.objects.filter(group_id=self.kwargs.get('pk'))
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
            )
        else:
            object_list = TroubleEvent.objects.all().order_by('id').reverse()
        return object_list

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('query', '')
        return ctx

class GroupBaseMixin(object):
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

class EventBaseMixin(object):
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
            print(date_type)
            if date_type == '1':
                date_delta1 = int(form.cleaned_data.get('date_delta1'))
                print(date_delta1)
                print((datetime.now() - timedelta(days=date_delta1), datetime.now))
                queryset = queryset.filter(
                    Q(
                        first_datetime__range=(
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
                        first_datetime__range=(
                            date2-timedelta(days=date_delta2),
                            date2+timedelta(days=date_delta2)
                        )
                    )
                )
            elif date_type == '3':
                date3s = form.cleaned_data.get('date3s')
                date3e = form.cleaned_data.get('date3e')
                queryset = queryset.filter(Q(first_datetime__range=(date3s, date3e)))
            causetype = form.cleaned_data.get('causetype')
            if not causetype == 'NOSELECT':
                queryset = queryset.filter(Q(causetype=causetype))
            vendor_status = form.cleaned_data.get('vendor_status')
            if not vendor_status == 'NOSELECT':
                queryset = queryset.filter(Q(vendor_status=vendor_status))
            handling_status = form.cleaned_data.get('handling_status')
            if not handling_status == 'NOSELECT':
                queryset = queryset.filter(Q(handling_status=handling_status))
        object_list = queryset
        return object_list

def change_operation(request):
    """Operation変更画面"""
    current_operation = Operation.objects.order_by('id').last()
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
    current_operation = Operation.objects.order_by('id').last()
    if current_operation:
        current_operation.end_time = form.cleaned_data.get('change_time')
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


class EventClassifyView(ListView):
    """イベント分類View"""
    template_name = 'event_classify.html'
    model = TroubleEvent

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
        context['current_operation'] = Operation.objects.order_by('id').last()
        return context

    def get_queryset(self):
        object_list = TroubleEvent.objects.order_by('start_time').reverse()[:5]
#	return render(request, 'home.html', {'current_operation':current_operation})
        return object_list
