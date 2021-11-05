""" PTOP view module """
import io
# from django.db.models.expressions import Subquery
import pytz
from datetime import datetime, timedelta
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormMixin
from django.utils import timezone
from django.utils.dateparse import parse_datetime
# from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
# from django.db.models import IntegerField, DurationField, FloatField
from django.db.models import Sum, F, Count
# from django.db.models.functions import Cast, TruncDay, TruncMonth, TruncYear, Trunc, Extract
from django.db.models.functions import Trunc
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django_pandas.io import read_frame
from reportlab.pdfgen import canvas
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
# from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import portrait
from reportlab.lib.units import mm
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import base64
import pandas as pd
import numpy as np
import re
import jaconv
import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
# from django.shortcuts import get_list_or_404
from dal import autocomplete
from .forms import AttachmentForm
from .forms import EventCreateForm
from .forms import GroupCreateForm
from .forms import GroupSearchForm
from .forms import AdvancedSearchForm
from .forms import EventSearchForm
from .forms import EventAdvancedSearchForm
from .forms import ChangeOperationForm
from .forms import OperationCreateForm
from .forms import StatisticsForm
from .forms import CommentCreateForm
from .forms import TroubleCommunicationSheetCreateForm
from .forms import GroupDetailForm
from .forms import AnnouncementCreateForm
from .forms import SupplyItemCreateForm
from .forms import SupplyItemStockForm
from .forms import SupplyRecordCreateForm
from .forms import SupplyItemUpdateForm
from .forms import SupplyItemExchangeForm
# from .models import User
from .models import Device, Error, Section
from .models import TroubleEvent, TroubleGroup
from .models import TroubleCommunicationSheet
from .models import Attachment
from .models import Comment
from .models import Operation
from .models import Announcement
from .models import EmailAddress
from .models import SupplyType, SupplyItem, SupplyRecord

matplotlib.use('Agg')


# Create your views here.

def get_tcs_address_list():
    # return [user.email for user in User.objects.filter(is_tcs_destination=True, email__isnull=False)]
    return [item.email for item in EmailAddress.objects.filter(is_tcs_destination=True, email__isnull=False).order_by('display_order')]


def standardize_character(str):
    """文字表記ゆれを統一する関数(カナは全角、英数字と記号は半角に変換)"""
    str = jaconv.z2h(str, kana=False, digit=True, ascii=True)
    str = jaconv.h2z(str, kana=True, digit=False, ascii=False)
    return str


def api_devices_get(request):
    """（不使用）サジェスト候補のデバイスIDをJSONで返す。"""
    keyword = request.GET.get('keyword')
    if keyword:
        post_list = [{'pk': item.pk, 'name': item.device_id} for item in Device.objects.filter(device_id__icontains=keyword)]
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
            return JsonResponse({'operation_type': ope.operation_type.id})
        else:
            return JsonResponse({'operation_type': None})
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
    searchForm = GroupSearchForm
    paginate_by = 10

    def get_paginate_by(self, queryset):
        return self.request.GET.get("paginate_by", self.paginate_by)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('query', '')
        default_data = {
            'query': self.request.GET.get('query'),
            'sort_by': self.request.GET.get('sort_by'),
            'paginate_by': self.request.GET.get('paginate_by'),
        }
        search_form = GroupSearchForm(initial=default_data)  # 検索フォーム
        ctx['search_form'] = search_form
        return ctx

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = TroubleGroup.objects.filter(
                Q(title__icontains=q_word)
                | Q(device__device_id__icontains=q_word)
                | Q(description__icontains=q_word)
                | Q(errors__error_code__icontains=q_word)
            )
        else:
            object_list = TroubleGroup.objects.all()
        object_list = object_list.order_by(self.request.GET.get('sort_by', '-first_datetime')).distinct()
        return object_list

    def get(self, request, *args, **kwargs):
        q_word = request.GET.get('query')
        p = re.compile('^(#|ID:|Id:|id:)(\d+)')
        m = p.match(q_word)
        if m:
            return redirect(f'../group_detail/{m.group(2)}/')
        else:
            return super().get(request, **kwargs)


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


class CommentCreateView(LoginRequiredMixin, CreateView):
    """新規Commentの作成"""
    model = Comment
    template_name = 'comment_create.html'
    form_class = CommentCreateForm
#    fields = '__all__'
    success_url = reverse_lazy('ptop:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
#        print(self.kwargs)
        posted_group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
        parent_id = self.request.GET.get('parent')
        if parent_id is not None:
            parent = get_object_or_404(Comment, pk=parent_id)
        else:
            parent = None
        context['base_group'] = self.kwargs.get('pk')
        context['form'] = CommentCreateForm(initial={
            'posted_group': posted_group,
            'parent': parent,
            'user': self.request.user,
        })
        return context

    def post(self, request, *args, **kwargs):
        # print(request)
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
            # form = CommentCreateForm(self.request.POST)
            # form.fields['attachments'].queryset = Attachment.objects.all().order_by('id')
            # print(self.request.POST)
            # print(form.fields['attachments'].queryset.reverse())
            return super().post(request, *args, **kwargs)


class PopupCommentCreateView(CommentCreateView):
    """ポップアップでのComment作成"""

    def form_valid(self, form):
        print(form)
        comment = form.save()
        print(comment.id)

        # 類型のタイムスタンプを更新する
#        Comment.object.filter(pk=comment.id).update(active=True)
#        comment.posted_group.modified_on = comment.posted_on
        comment.posted_group.active = True
        comment.posted_group.save()

        return render(self.request, 'close_reload.html')


class GroupDetailView(FormMixin, DetailView):
    """TroubleGroup詳細画面"""
    template_name = 'group_detail.html'
    model = TroubleGroup
    form_class = GroupDetailForm
    fields = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
#        context['events'] = TroubleEvent.objects.filter(group_id=self.kwargs.get('pk'))
        startpath = '/' + context.get('object').path.split('/')[1] + '/'
#        print(startpath)
        display_range = self.request.GET.get('display_range')
        if display_range == 'only_myself':
            context['events'] = TroubleEvent.objects.filter(group__path__exact=context.get('object').path).order_by('-start_time')
        elif display_range == 'myself_and_child':
            context['events'] = TroubleEvent.objects.filter(group__path__startswith=context.get('object').path).order_by('-start_time')
        else:
            context['events'] = TroubleEvent.objects.filter(group__path__startswith=startpath).order_by('-start_time')

        context['child_group'] = TroubleGroup.objects.filter(path__startswith=startpath)
        context['parent_comments'] = context.get('object').comments.filter(parent__isnull=True)
        context['frequency_week_1'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=7), timezone.now())).count()
        context['frequency_week_2'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=14), timezone.now() - timezone.timedelta(days=7))).count()
        context['frequency_week_3'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=21), timezone.now() - timezone.timedelta(days=14))).count()
        context['frequency_week_4'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=28), timezone.now() - timezone.timedelta(days=21))).count()
        context['frequency_month_1'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=30), timezone.now())).count()
        context['frequency_month_2'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=60), timezone.now() - timezone.timedelta(days=30))).count()
        context['frequency_month_3'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=90), timezone.now() - timezone.timedelta(days=60))).count()
        context['frequency_month_4'] = context['events'].filter(start_time__range=(timezone.now() - timezone.timedelta(days=120), timezone.now() - timezone.timedelta(days=90))).count()

        default_data = {
            'display_range': self.request.GET.get('display_range'),
        }
        form = GroupDetailForm(initial=default_data)  # 検索フォーム
        context['form'] = form
        # print(context['frequency_week_3'])
        return context


class EventDetailView(DetailView):
    """TroubleEvent詳細画面"""
    template_name = 'event_detail.html'
    model = TroubleEvent


class TroubleCommunicationSheetPDFView(DetailView):
    """不具合連絡票PDF作成画面"""
    model = TroubleGroup

    def get(self, request, *args, **kwargs):

        obj = self.get_object()
        filename = '装置不具合連絡票TR%s(%s).pdf' % (obj.classify_id, obj.title)  # 出力ファイル名
        title = '装置不具合連絡票TR%s(%s).pdf' % (obj.classify_id, obj.title)
        font_name = 'HeiseiKakuGo-W5'  # フォント
        is_bottomup = True

        # PDF出力
        response = HttpResponse(status=200, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)  # ダウンロードする場合
        # response['Content-Disposition'] = 'filename="{}"'.format(filename)  # 画面に表示する場合
        # A4縦書きのpdfを作る
        size = portrait(A4)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer,
                                rightMargin=20 * mm,
                                leftMargin=20 * mm,
                                topMargin=20 * mm,
                                bottomMargin=20 * mm,
                                pagesize=size,
                                title=filename[:-4])
        elements = []
        # pdfを描く場所を作成：位置を決める原点は左上にする(bottomup)
        # デフォルトの原点は左下
        p = canvas.Canvas(response, pagesize=size, bottomup=is_bottomup)
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        p.setFont(font_name, 16)  # フォントを設定
        # pdfのタイトルを設定
        p.setTitle(title)
        first_datetime = None
        first_downtime = 0
        first_delaytime = 0
        if obj.first_event() is not None:
            first_datetime = timezone.localtime(obj.first_event().start_time)
            if obj.first_event().downtime is not None:
                first_downtime = obj.first_event().downtime
            else:
                first_downtime = 0
            if obj.first_event().delaytime is not None:
                first_delaytime = obj.first_event().delaytime
            else:
                first_delaytime = 0
        if first_downtime is None:
            first_downtime = 0
        if first_delaytime is None:
            first_delaytime = 0

        errorcode_str = ', '.join(list(obj.errors.values_list('error_code', flat=True)))
        if first_datetime is not None:
            first_datetime_str = first_datetime.strftime('%Y/%m/%d %H:%M')
        else:
            first_datetime_str = ''

        style_title = ParagraphStyle(name='Normal', fontName=font_name, fontSize=18, leading=24, alignment=TA_CENTER)
        style_signature = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=16, alignment=TA_RIGHT)
        style_table = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=14, alignment=TA_LEFT)

        # 表の情報
        data = [
            ['題名', obj.title],
            ['治療可否の状態', obj.treatment_status.name if obj.treatment_status is not None else '未入力'],
            ['影響範囲', obj.effect_scope.name if obj.effect_scope is not None else '未入力'],
            ['対処緊急度', obj.urgency.name if obj.urgency is not None else '未入力'],
            ['初発日時', first_datetime_str],
            ['発生回数', '%d回' % obj.num_events()],
            ['初回停止時間', '%d分(遅延%d分)' % (first_downtime, first_delaytime)],
            ['平均停止時間', '%.1f分' % obj.average_downtime() if obj.average_downtime() is not None else '未入力'],
            ['デバイスID', '%s (%s)' % (obj.device.device_id, obj.device.name)],
            ['内容', Paragraph(obj.description, style_table)],
            ['エラーコード', errorcode_str],
            ['直前の操作', Paragraph(obj.trigger, style_table)],
            ['原因', Paragraph(obj.cause, style_table)],
            ['応急処置', Paragraph(obj.common_action, style_table)],
            ['要望項目', ', '.join(list(obj.require_items.values_list('name', flat=True)))],
            ['要望詳細', Paragraph(obj.require_detail if obj.require_detail is not None else '', style_table)],
        ]
        table = Table(data, (35 * mm, 130 * mm), None, hAlign='LEFT')

        # TableStyleを使って、Tableの装飾をします。
        table.setStyle(TableStyle([
            # 表で使うフォントとそのサイズを設定
            ('FONT', (0, 0), (-1, -1), font_name, 12),
            # 四角に罫線を引いて、0.5の太さで、色は黒
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            # 四角の内側に格子状の罫線を引いて、0.25の太さで、色は黒
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            # セルの縦文字位置
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ("ALIGN", (0, 0), (-1, -1), 'LEFT'),
        ]))
#        elements.append(Paragraph('山形大学医学部東日本重粒子センター　重粒子線治療装置', style_title))
        elements.append(Paragraph('装置不具合連絡票', style_title))
        elements.append(Paragraph('連絡票ID: TR%s' % obj.classify_id, style_title))
        elements.append(Paragraph('山形大学医学部東日本重粒子センター', style_signature))
        elements.append(Paragraph('発行者: %s' % obj.classify_operator.fullname(), style_signature))
        elements.append(Paragraph('発行日時: %s' % datetime.now().strftime('%Y/%m/%d %H:%M'), style_signature))
        elements.append(table)
        table.canv = p
        w, h = table.wrap(0, 0)
        print(w / mm, h / mm)

        table.wrapOn(p, 25 * mm, 260 * mm)
        table.drawOn(p, 25 * mm, 260 * mm - h)
        p.drawString(25 * mm, 280 * mm, '山形大学医学部東日本重粒子センター　重粒子線治療装置')
        p.drawString(25 * mm, 272 * mm, '装置不具合連絡票')
        p.drawString(25 * mm, 264 * mm, '連絡票ID: TR%s' % obj.id)

        doc.build(elements)
#        doc.title(filemame)
        response = HttpResponse(status=200, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)  # ダウンロードする場合

#        response = HttpResponse(status=200, content_type='application/pdf')
#        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)  # ダウンロードする場合
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='{}'.format(filename))
#        response.write(buffer.getvalue())
#        buffer.close()
#        return response

    def _draw(self, p):
        pass


class TroubleCommunicationSheetCreateView(LoginRequiredMixin, CreateView):
    '''不具合連絡票作成画面'''
    template_name = 'trouble_communication_sheet_create.html'
    model = TroubleCommunicationSheet
    form_class = TroubleCommunicationSheetCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:group_detail', kwargs={'pk': self.request.GET.get('group')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = get_object_or_404(TroubleGroup, pk=self.request.GET.get('group'))

        # versionの決定
        version = 0
        sheets = obj.troublecommunicationsheet_set.all()
        if sheets.count() == 0:
            version = 1
        else:
            version = sheets.order_by('-created_on')[0].version + 1

        filename = f'装置不具合連絡票TR{obj.classify_id}({obj.title})ver{version}.pdf'  # 出力ファイル名
        title = filename
        font_name = 'HeiseiKakuGo-W5'  # フォント
        is_bottomup = True

        # PDF出力
        response = HttpResponse(status=200, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)  # ダウンロードする場合
        # response['Content-Disposition'] = 'filename="{}"'.format(filename)  # 画面に表示する場合
        # A4縦書きのpdfを作る
        size = portrait(A4)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer,
                                rightMargin=20 * mm,
                                leftMargin=20 * mm,
                                topMargin=20 * mm,
                                bottomMargin=20 * mm,
                                pagesize=size,
                                title=filename[:-4])
        elements = []
        # pdfを描く場所を作成：位置を決める原点は左上にする(bottomup)
        # デフォルトの原点は左下
        p = canvas.Canvas(response, pagesize=size, bottomup=is_bottomup)
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        p.setFont(font_name, 16)  # フォントを設定
        # pdfのタイトルを設定
        p.setTitle(title)
        if obj.first_event() is not None:
            first_datetime = timezone.localtime(obj.first_event().start_time)
            if obj.first_event().downtime is not None:
                first_downtime = obj.first_event().downtime
            else:
                first_downtime = 0
            if obj.first_event().downtime is not None:
                first_delaytime = obj.first_event().delaytime
            else:
                first_delaytime = 0
        else:
            first_datetime = None
            first_downtime = 0
            first_delaytime = 0

        errorcode_str = ', '.join(list(obj.errors.values_list('error_code', flat=True)))
        if first_datetime is not None:
            first_datetime_str = first_datetime.strftime('%Y/%m/%d %H:%M')
        else:
            first_datetime_str = ''

        style_title = ParagraphStyle(name='Normal', fontName=font_name, fontSize=18, leading=24, alignment=TA_CENTER)
        style_signature = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=16, alignment=TA_RIGHT)
        style_table = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=14, alignment=TA_LEFT)

        # 表の情報
        data = [
            ['題名', obj.title],
            ['治療可否の状態', obj.treatment_status.name if obj.treatment_status is not None else '未入力'],
            ['影響範囲', obj.effect_scope.name if obj.effect_scope is not None else '未入力'],
            ['対処緊急度', obj.urgency.name if obj.urgency is not None else '未入力'],
            ['初発日時', first_datetime_str],
            ['発生回数', '%d回' % obj.num_events()],
            ['初回停止時間', '%d分(遅延%d分)' % (first_downtime, first_delaytime)],
            ['平均停止時間', '%.1f分' % obj.average_downtime() if obj.average_downtime() is not None else '未入力'],
            ['デバイスID', '%s (%s)' % (obj.device.device_id, obj.device.name)],
            ['内容', Paragraph(obj.description, style_table)],
            ['エラーコード', errorcode_str],
            ['直前の操作', Paragraph(obj.trigger, style_table)],
            ['原因', Paragraph(obj.cause, style_table)],
            ['応急処置', Paragraph(obj.common_action, style_table)],
            ['要望項目', ', '.join(list(obj.require_items.values_list('name', flat=True)))],
            ['要望詳細', Paragraph(obj.require_detail if obj.require_detail is not None else '', style_table)],
        ]
        table = Table(data, (35 * mm, 130 * mm), None, hAlign='LEFT')

        # TableStyleを使って、Tableの装飾をします。
        table.setStyle(TableStyle([
            # 表で使うフォントとそのサイズを設定
            ('FONT', (0, 0), (-1, -1), font_name, 12),
            # 四角に罫線を引いて、0.5の太さで、色は黒
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            # 四角の内側に格子状の罫線を引いて、0.25の太さで、色は黒
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            # セルの縦文字位置
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ("ALIGN", (0, 0), (-1, -1), 'LEFT'),
        ]))
#        elements.append(Paragraph('山形大学医学部東日本重粒子センター　重粒子線治療装置', style_title))
        elements.append(Paragraph('装置不具合連絡票', style_title))
        elements.append(Paragraph(f'連絡票ID: TR{obj.classify_id} 第{version}版', style_title))
        elements.append(Paragraph('山形大学医学部東日本重粒子センター', style_signature))
        elements.append(Paragraph(f'発行者: {self.request.user.fullname()}', style_signature))
        elements.append(Paragraph(f'発行日時: {datetime.now().strftime("%Y/%m/%d %H:%M")}', style_signature))
        elements.append(table)
        if obj.comments.count() > 0:
            elements.append(Paragraph('コメント', style_table))
            for comment in obj.comments.order_by('posted_on'):
                elements.append(Paragraph(f'・{comment.description} - {comment.posted_on.strftime("%Y/%m/%d %H:%M")} {comment.user.fullname()}', style_table))

        doc.build(elements)
        buffer.seek(0)

        pdf_bytes = buffer.getvalue()
        pdf_b64 = base64.b64encode(pdf_bytes)
        pdf_b64 = pdf_b64.decode('utf-8')

#        print(pdf_b64)
        context = super().get_context_data(**kwargs)
        context['group'] = obj
        context['pdf_file'] = pdf_b64
        context['pdf_filename'] = filename
        context['version'] = version
        context['form'] = TroubleCommunicationSheetCreateForm(initial={
            'group': obj,
            'version': version,
            'file_base64': pdf_b64,
            'filename': filename,
            'user': self.request.user,
        })
        context['mailto_list'] = get_tcs_address_list()
#        print(context['form'])
        return context

    def post(self, request, *args, **kwargs):

        group = get_object_or_404(TroubleGroup, pk=request.POST['group'])
        form = self.form_class(request.POST)
        # print(self.request.GET.get('pdf_filename'))
        pdf_b64 = request.POST['file_base64']
        filename = request.POST['filename']
        if 'is_sendmail' in request.POST:
            is_sendmail = True
        else:
            is_sendmail = False

        if group.first_event() is not None:
            first_datetime = timezone.localtime(group.first_event().start_time)
        else:
            first_datetime = None
        if first_datetime is not None:
            first_datetime_str = first_datetime.strftime('%Y/%m/%d %H:%M')
        else:
            first_datetime_str = ''

        if form.is_valid():
            ver_form = request.POST['version']
            if TroubleCommunicationSheet.objects.filter(group=group, version=ver_form):
                print(f'TR{group.classify_id}-{ver_form} already exists.')
                return redirect('ptop:group_detail', pk=group.pk)

            obj = form.save(commit=False)
            obj.file = ContentFile(base64.b64decode(pdf_b64), name=filename)
            obj.save()

            if is_sendmail is True:
                mail = EmailMessage(
                    f'EJHIC装置不具合連絡票 TR{group.classify_id} 第{obj.version}版 発行({group.title})',
                    f'''皆様

　装置不具合連絡票 TR{group.classify_id} (第{obj.version}版) を添付の通り発行いたします。

PT-DOM URL:
http://133.24.154.31/group_detail/{group.id}/

題名: {group.title}
初発日時: {first_datetime_str}
内容: {group.description}
要望項目: {', '.join(list(group.require_items.values_list('name', flat=True)))}
要望詳細: {group.require_detail if group.require_detail is not None else ''}

発行者: {self.request.user}

-- 
本メールはPT-DOMからの自動送信メールです。
問い合わせは
想田光 souda@med.id.yamagata-u.ac.jp
までお願いいたします。
''',
                    self.request.user.email,
                    get_tcs_address_list(),
                )

                mail.attach(filename, base64.b64decode(pdf_b64), 'application/pdf')

                mail.send()

            return redirect('ptop:group_detail', pk=group.pk)


class TroubleCommunicationSheetDispatchView(DetailView):
    '''不具合連絡票PDF発行画面'''
    template_name = 'trouble_communication_sheet_dispatch.html'
    model = TroubleGroup

#    def get(self, request, *args, **kwargs):
    def get_context_data(self, **kwargs):

        obj = self.get_object()
        filename = '装置不具合連絡票TR%s(%s).pdf' % (obj.classify_id, obj.title)  # 出力ファイル名
        title = '装置不具合連絡票TR%s(%s).pdf' % (obj.classify_id, obj.title)
        font_name = 'HeiseiKakuGo-W5'  # フォント
        is_bottomup = True

        # PDF出力
        response = HttpResponse(status=200, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)  # ダウンロードする場合
        # response['Content-Disposition'] = 'filename="{}"'.format(filename)  # 画面に表示する場合
        # A4縦書きのpdfを作る
        size = portrait(A4)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer,
                                rightMargin=20 * mm,
                                leftMargin=20 * mm,
                                topMargin=20 * mm,
                                bottomMargin=20 * mm,
                                pagesize=size,
                                title=filename[:-4])
        elements = []
        # pdfを描く場所を作成：位置を決める原点は左上にする(bottomup)
        # デフォルトの原点は左下
        p = canvas.Canvas(response, pagesize=size, bottomup=is_bottomup)
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        p.setFont(font_name, 16)  # フォントを設定
        # pdfのタイトルを設定
        p.setTitle(title)
        if obj.first_event() is not None:
            first_datetime = timezone.localtime(obj.first_event().start_time)
            if obj.first_event().downtime is not None:
                first_downtime = obj.first_event().downtime
            else:
                first_downtime = 0
            if obj.first_event().downtime is not None:
                first_delaytime = obj.first_event().delaytime
            else:
                first_delaytime = 0
        else:
            first_datetime = None
            first_downtime = 0
            first_delaytime = 0

        errorcode_str = ', '.join(list(obj.errors.values_list('error_code', flat=True)))
        if first_datetime is not None:
            first_datetime_str = first_datetime.strftime('%Y/%m/%d %H:%M')
        else:
            first_datetime_str = ''

        style_title = ParagraphStyle(name='Normal', fontName=font_name, fontSize=18, leading=24, alignment=TA_CENTER)
        style_signature = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=16, alignment=TA_RIGHT)
        style_table = ParagraphStyle(name='Normal', fontName=font_name, fontSize=12, leading=14, alignment=TA_LEFT)

        # 表の情報
        data = [
            ['題名', obj.title],
            ['治療可否の状態', obj.treatment_status.name if obj.treatment_status is not None else '未入力'],
            ['影響範囲', obj.effect_scope.name if obj.effect_scope is not None else '未入力'],
            ['対処緊急度', obj.urgency.name if obj.urgency is not None else '未入力'],
            ['初発日時', first_datetime_str],
            ['発生回数', '%d回' % obj.num_events()],
            ['初回停止時間', '%d分(遅延%d分)' % (first_downtime, first_delaytime)],
            ['平均停止時間', '%.1f分' % obj.average_downtime() if obj.average_downtime() is not None else '未入力'],
            ['デバイスID', '%s (%s)' % (obj.device.device_id, obj.device.name)],
            ['内容', Paragraph(obj.description, style_table)],
            ['エラーコード', errorcode_str],
            ['直前の操作', Paragraph(obj.trigger, style_table)],
            ['原因', Paragraph(obj.cause, style_table)],
            ['応急処置', Paragraph(obj.common_action, style_table)],
            ['要望項目', ', '.join(list(obj.require_items.values_list('name', flat=True)))],
            ['要望詳細', Paragraph(obj.require_detail if obj.require_detail is not None else '', style_table)],
        ]
        table = Table(data, (35 * mm, 130 * mm), None, hAlign='LEFT')

        # TableStyleを使って、Tableの装飾をします。
        table.setStyle(TableStyle([
            # 表で使うフォントとそのサイズを設定
            ('FONT', (0, 0), (-1, -1), font_name, 12),
            # 四角に罫線を引いて、0.5の太さで、色は黒
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            # 四角の内側に格子状の罫線を引いて、0.25の太さで、色は黒
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            # セルの縦文字位置
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ("ALIGN", (0, 0), (-1, -1), 'LEFT'),
        ]))
        # elements.append(Paragraph('山形大学医学部東日本重粒子センター　重粒子線治療装置', style_title))
        elements.append(Paragraph('装置不具合連絡票', style_title))
        elements.append(Paragraph('連絡票ID: TR%s' % obj.classify_id, style_title))
        elements.append(Paragraph('山形大学医学部東日本重粒子センター', style_signature))
        elements.append(Paragraph('発行者: %s' % obj.classify_operator.fullname(), style_signature))
        elements.append(Paragraph('発行日時: %s' % datetime.now().strftime('%Y/%m/%d %H:%M'), style_signature))
        elements.append(table)
        table.canv = p
        w, h = table.wrap(0, 0)
        print(w / mm, h / mm)

        table.wrapOn(p, 25 * mm, 260 * mm)
        table.drawOn(p, 25 * mm, 260 * mm - h)
        p.drawString(25 * mm, 280 * mm, '山形大学医学部東日本重粒子センター　重粒子線治療装置')
        p.drawString(25 * mm, 272 * mm, '装置不具合連絡票')
        p.drawString(25 * mm, 264 * mm, '連絡票ID: TR%s' % obj.id)

        doc.build(elements)
        buffer.seek(0)

        pdf_bytes = buffer.getvalue()
        pdf_b64 = base64.b64encode(pdf_bytes)
        pdf_b64 = pdf_b64.decode('utf-8')

        # print(pdf_b64)
        context = super().get_context_data(**kwargs)
        context['pdf_file'] = pdf_b64
        context['pdf_filename'] = filename
        return context


class TroubleCommunicationSheetView(DetailView):
    """不具合連絡票詳細画面"""
    template_name = 'trouble_communication_sheet.html'
    model = TroubleEvent


class LognoteSheetView(DetailView):
    """ログノート帳票画面"""
    template_name = 'lognote_sheet.html'
    model = TroubleEvent


class TroubleEventDetail(DetailView):
    """TroubleEvent詳細画面(旧ver)"""
    template_name = 'event.html'
    model = TroubleEvent


class TroubleEventList(ListView):
    """TroubleEventList画面"""
    template_name = 'eventlist.html'
    model = TroubleEvent
    searchForm = EventSearchForm
    paginate_by = 10

    def get_paginate_by(self, queryset):
        return self.request.GET.get("paginate_by", self.paginate_by)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('query', '')
        default_data = {
            'query': self.request.GET.get('query'),
            'sort_by': self.request.GET.get('sort_by'),
            'paginate_by': self.request.GET.get('paginate_by'),
        }
        search_form = EventSearchForm(initial=default_data)  # 検索フォーム
        ctx['search_form'] = search_form
        return ctx

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = TroubleEvent.objects.filter(
                Q(title__icontains=q_word)
                | Q(device__device_id__icontains=q_word)
                | Q(description__icontains=q_word)
                | Q(errors__error_code__icontains=q_word)
            )
        else:
            object_list = TroubleEvent.objects.all()
        object_list = object_list.order_by(self.request.GET.get('sort_by', '-start_time')).distinct()
        return object_list

    def get(self, request, *args, **kwargs):
        q_word = request.GET.get('query')
        if q_word:
            p = re.compile('^(#|ID:|Id:|id:)(\d+)')
            m = p.match(q_word)
            if m:
                return redirect(f'../event_detail/{m.group(2)}/')
            else:
                return super().get(request, **kwargs)
        else:
            return super().get(request, **kwargs)


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
            return redirect('ptop:group_detail', pk=obj.pk)
#            return redirect('ptop:unapproved_event_list')

        elif 'child_group' in self.request.path:
            event_pk = request.GET.get('event_pk')
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
                    return redirect('ptop:group_detail', pk=obj.pk)
            else:
                form = self.form_class(request.POST)
                if form.is_valid():
                    obj = form.save()
                    return redirect('ptop:group_detail', pk=obj.pk)

            return redirect('ptop:home')

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
            form = EventCreateForm(self.request.POST)
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
            'title': event.title,
            'device': event.device,
            'description': event.description,
            'cause': event.cause,
            'trigger': event.trigger,
            'errors': event.errors.all(),
            'first_datetime': event.start_time,
            'common_action': event.temporary_action,
            'urgency': event.urgency,
            'treatment_status': event.treatment_status,
            'effect_scope': event.effect_scope,
            'classify_operator': self.request.user,
        })
        return context


class ChildGroupCreateView(GroupBaseMixin, CreateView):
    """あるGroupから子Groupを作る画面"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
        event_pk = self.request.GET.get('event_pk', '')

        if event_pk:
            event = get_object_or_404(TroubleEvent, pk=event_pk)
            context['form'] = GroupCreateForm(initial={
                'title': parent_group.title + '(sub)',
                'device': event.device,
                'description': event.description,
                'trigger': event.trigger,
                'cause': event.cause,
                'causetype': parent_group.causetype,
                'errors': event.errors.all(),
                'common_action': event.temporary_action,
                'first_datetime': event.start_time,
                'urgency': event.urgency,
                'treatment_status': event.treatment_status,
                'effect_scope': event.effect_scope,
                'classify_operator': self.request.user,
                'path': parent_group.path,
            })
        else:
            context['form'] = GroupCreateForm(initial={
                'title': parent_group.title + '(sub)',
                'device': parent_group.device,
                'description': parent_group.description,
                'trigger': parent_group.trigger,
                'cause': parent_group.cause,
                'causetype': parent_group.causetype,
                'errors': parent_group.errors.all(),
                'common_action': parent_group.common_action,
                'first_datetime': parent_group.first_datetime,
                'permanent_action': parent_group.permanent_action,
                'urgency': parent_group.urgency,
                'treatment_status': parent_group.treatment_status,
                'effect_scope': parent_group.effect_scope,
                'classify_operator': self.request.user,
                'path': parent_group.path,
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
            'title': event.title,
            'group': event.group,
            'device': event.device,
            'description': event.description,
            'cause': event.cause,
            'trigger': event.trigger,
            'temporary_action': event.temporary_action,
            'input_operator': self.request.user,
            'errors': [i.id for i in event.errors.all()],
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
            'title': group.title,
            'group': group,
            'device': group.device,
            'description': group.description,
            'cause': group.cause,
            'input_operator': self.request.user,
            'temporary_action': group.common_action,
            'errors': [i.id for i in group.errors.all()],
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
            'input_operator': self.request.user,
        })
        return context


class EventUpdateView(EventBaseMixin, UpdateView):
    """Event編集画面"""
    model = TroubleEvent
    form_class = EventCreateForm
    template_name = 'create_event.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(self.get_object().attachments)
        context['attachments'] = self.object.attachments
        return context


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
    paginate_by = 10

    def get_paginate_by(self, queryset):
        return self.request.GET.get("paginate_by", self.paginate_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.GET.get('date_type'):
            date_type = '0'
        else:
            date_type = self.request.GET.get('date_type'),
        default_data = {
            'classify_id': self.request.GET.get('classify_id'),
            'title': self.request.GET.get('title'),
            'description': self.request.GET.get('description'),
            'cause': self.request.GET.get('cause'),
            'device': self.request.GET.get('device'),
            'error': self.request.GET.get('error'),
            'date_type': date_type,
            'date_delta1': self.request.GET.get('date_delta1'),
            'date2': self.request.GET.get('date2'),
            'date_delta2': self.request.GET.get('date_delta2'),
            'date3s': self.request.GET.get('date3s'),
            'date3e': self.request.GET.get('date3e'),
            'causetype': self.request.GET.get('causetype'),
            'vendor_status': self.request.GET.get('vendor_status'),
            'handling_status': self.request.GET.get('handling_status'),
            'sort_by': self.request.GET.get('sort_by'),
            'paginate_by': self.request.GET.get('paginate_by'),
        }
        search_form = AdvancedSearchForm(initial=default_data)  # 検索フォーム
        context['search_form'] = search_form
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
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
            cause = form.cleaned_data.get('cause')
            if cause:
                queryset = queryset.filter(Q(cause__icontains=cause))
            error = form.cleaned_data.get('error')
            if error:
                queryset = queryset.filter(Q(errors__error_code__icontains=error))
            date_type = form.cleaned_data.get('date_type')
            print(date_type)
            if date_type == '1':
                if form.cleaned_data.get('date_delta1'):
                    date_delta1 = int(form.cleaned_data.get('date_delta1'))
                else:
                    date_delta1 = 0
                print(date_delta1)
                print((datetime.now() - timedelta(days=date_delta1), datetime.now))
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            datetime.now().date() - timedelta(days=date_delta1),
                            datetime.now()
                        )
                    )
                )
            elif date_type == '2':
                date2 = form.cleaned_data.get('date2')
                if not date2:
                    date2 = timezone.now().date()
                if form.cleaned_data.get('date_delta2'):
                    date_delta2 = int(form.cleaned_data.get('date_delta2'))
                else:
                    date_delta2 = 0
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            date2 - timedelta(days=date_delta2),
                            date2 + timedelta(days=date_delta2 + 1)
                        )
                    )
                )
            elif date_type == '3':
                date3s = form.cleaned_data.get('date3s')
                if not date3s:
                    date3s = datetime(2019, 4, 1)
                date3e = form.cleaned_data.get('date3e')
                if not date3e:
                    date3e = timezone.now()
                queryset = queryset.filter(Q(start_time__range=(date3s, date3e)))
            causetype = form.cleaned_data.get('causetype')
            if causetype:
                queryset = queryset.filter(Q(causetype=causetype))
            vendor_status = form.cleaned_data.get('vendor_status')
            if vendor_status:
                queryset = queryset.filter(Q(vendor_status=vendor_status))
            handling_status = form.cleaned_data.get('handling_status')
            if handling_status:
                queryset = queryset.filter(Q(handling_status=handling_status))
        object_list = queryset.order_by(self.request.GET.get('sort_by', '-first_datetime'))
        return object_list


class EventAdvancedSearchView(ListView):
    """Event詳細検索画面"""
    template_name = 'event_advanced_search.html'
    searchForm = EventAdvancedSearchForm
    model = TroubleEvent
    paginate_by = 10

    def get_paginate_by(self, queryset):
        return self.request.GET.get("paginate_by", self.paginate_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.GET.get('date_type'):
            date_type = '0'
        else:
            date_type = self.request.GET.get('date_type'),
        default_data = {
            'id': self.request.GET.get('id'),
            'title': self.request.GET.get('title'),
            'description': self.request.GET.get('description'),
            'cause': self.request.GET.get('cause'),
            'device': self.request.GET.get('device'),
            'error': self.request.GET.get('error'),
            'date_type': date_type,
            'date_delta1': self.request.GET.get('date_delta1'),
            'date2': self.request.GET.get('date2'),
            'date_delta2': self.request.GET.get('date_delta2'),
            'date3s': self.request.GET.get('date3s'),
            'date3e': self.request.GET.get('date3e'),
            'downtime_low': self.request.GET.get('downtime_low'),
            'downtime_high': self.request.GET.get('downtime_high'),
            'delaytime_low': self.request.GET.get('delaytime_low'),
            'delaytime_high': self.request.GET.get('delaytime_high'),
            'sort_by': self.request.GET.get('sort_by'),
            'paginate_by': self.request.GET.get('paginate_by'),
        }
        search_form = EventAdvancedSearchForm(initial=default_data)  # 検索フォーム
        context['search_form'] = search_form
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.search_form = EventAdvancedSearchForm(self.request.GET or None)
        if form.is_valid():
            id = form.cleaned_data.get('id')
            if id:
                queryset = queryset.filter(Q(id__exact=id))
            title = form.cleaned_data.get('title')
            if title:
                queryset = queryset.filter(Q(title__icontains=title))
            description = form.cleaned_data.get('description')
            if description:
                queryset = queryset.filter(Q(description__icontains=description))
            device = form.cleaned_data.get('device')
            if device:
                queryset = queryset.filter(Q(device__device_id__icontains=device))
            cause = form.cleaned_data.get('cause')
            if cause:
                queryset = queryset.filter(Q(cause__icontains=cause))
            error = form.cleaned_data.get('error')
            if error:
                queryset = queryset.filter(Q(errors__error_code__icontains=error))
            date_type = form.cleaned_data.get('date_type')
            print(date_type)
            if date_type == '1':
                if form.cleaned_data.get('date_delta1'):
                    date_delta1 = int(form.cleaned_data.get('date_delta1'))
                else:
                    date_delta1 = 0
                print(date_delta1)
                print((datetime.now() - timedelta(days=date_delta1), datetime.now))
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            datetime.now().date() - timedelta(days=date_delta1),
                            datetime.now()
                        )
                    )
                )
            elif date_type == '2':
                date2 = form.cleaned_data.get('date2')
                if not date2:
                    date2 = timezone.now().date()
                if form.cleaned_data.get('date_delta2'):
                    date_delta2 = int(form.cleaned_data.get('date_delta2'))
                else:
                    date_delta2 = 0
                queryset = queryset.filter(
                    Q(
                        start_time__range=(
                            date2 - timedelta(days=date_delta2),
                            date2 + timedelta(days=date_delta2 + 1)
                        )
                    )
                )
            elif date_type == '3':
                date3s = form.cleaned_data.get('date3s')
                if not date3s:
                    date3s = datetime(2019, 4, 1)
                date3e = form.cleaned_data.get('date3e')
                if not date3e:
                    date3e = timezone.now()
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

        sort_by = self.request.GET.get('sort_by', default='-start_time')
        object_list = queryset.order_by(sort_by, '-start_time')
        return object_list

    def export_csv(request):

        queryset = EventAdvancedSearchView.get_queryset()
        df = read_frame(queryset)

        response = HttpResponse(content_type='text/csv; charset=cp932')
        filename = 'EventAdvancedSearchResult_%s.csv' % (datetime.today().strftime('%Y%m%d-%H%M'))
        print(filename)
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        df.to_csv(path_or_buf=response, encoding='utf_8_sig')
        print(response)
        return response


class OperationListView(ListView):
    """OperationList画面"""
    template_name = 'operation_list.html'
    model = Operation
    paginate_by = 10

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            try:
                d = datetime.strptime(q_word, '%Y/%m/%d')
                object_list = Operation.objects.filter(Q(start_time__date=d)).order_by('start_time').reverse()
            except ValueError:
                object_list = Operation.objects.filter(
                    Q(operation_type__name__icontains=q_word)
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
            & ((Q(start_time__lt=start) & Q(end_time__gt=start)) | (Q(start_time__lt=end) & Q(end_time__gt=end)))
        )
        if query_set.first():
            print(query_set)
            return render(
                request,
                'create_operation.html',
                {'form': OperationCreateForm(request.POST), 'overlapped_oparations': query_set}
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
    treat_flag = False
    pqa_flag = False
    if current_operation:
        if current_operation.operation_type.name == '治療':
            treat_flag = True
        elif current_operation.operation_type.name == '患者QA':
            pqa_flag = True
        return render(
            request,
            'change_operation.html',
            {
                'current_operation': current_operation,
                'change_form': ChangeOperationForm,
                'treat_flag': treat_flag,
                'pqa_flag': pqa_flag,
            }
        )
    else:
        return render(
            request,
            'change_operation.html',
            {'current_operation': None, 'change_form': ChangeOperationForm}
        )


def change_operation_execute(request):
    """Operation変更実行"""
    form = ChangeOperationForm(data=request.POST)
    form.full_clean()
    current_operation = Operation.objects.order_by('start_time').last()
    if current_operation:
        current_operation.end_time = form.cleaned_data.get('change_time')
        current_operation.operation_time = (current_operation.end_time - current_operation.start_time).total_seconds() / 60.0
        (current_operation.num_treat_hc1, ) = form.cleaned_data.get('num_treat_hc1'),
        (current_operation.num_treat_gc2, ) = form.cleaned_data.get('num_treat_gc2'),
        (current_operation.num_qa_hc1, ) = form.cleaned_data.get('num_qa_hc1'),
        (current_operation.num_qa_gc2, ) = form.cleaned_data.get('num_qa_gc2'),
        (current_operation.comment, ) = form.cleaned_data.get('comment'),
        if current_operation.num_treat_hc1 is None:
            current_operation.num_treat_hc1 = 0
        if current_operation.num_treat_gc2 is None:
            current_operation.num_treat_gc2 = 0
        if current_operation.num_qa_hc1 is None:
            current_operation.num_qa_hc1 = 0
        if current_operation.num_qa_gc2 is None:
            current_operation.num_qa_gc2 = 0
        current_operation.save()
        new_operation = Operation.objects.create(
            operation_type=form.cleaned_data.get('operation_type'),
            start_time=form.cleaned_data.get('change_time'),
            # num_treat_hc1=form.cleaned_data.get('num_treat_hc1'),
            # num_treat_gc2=form.cleaned_data.get('num_treat_gc2'),
            # num_qa_hc1=form.cleaned_data.get('num_qa_hc1'),
            # num_qa_gc2=form.cleaned_data.get('num_qa_gc2'),
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
        return Announcement.objects.all().order_by('-posted_time')


class AnnouncementDetailView(DetailView):
    """Announcement詳細画面"""
    template_name = 'announcement_detail.html'
    model = Announcement


class AnnouncementUpdateView(LoginRequiredMixin, UpdateView):
    """Announcement作成画面"""
    template_name = 'announcement_create.html'
    model = Announcement
    form_class = AnnouncementCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:announcement_detail', kwargs={'pk': self.object.id})


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
            'user': self.request.user,
        })
        return context


class CommentBaseMixin(LoginRequiredMixin, object):
    """Comment作成/更新画面"""
    template_name = 'comment_create.html'
    model = Comment
    form_class = CommentCreateForm

    def get_success_url(self):
        # print(self.object.posted_group.id)
        return reverse_lazy('ptop:group_detail', kwargs={'pk': self.object.posted_group.id})

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
            form = CommentCreateForm(self.request.POST)
#            form.fields['attachments'].queryset = Attachment.objects.all().order_by('id')
#            print(self.request.POST)
#            print(form.fields['attachments'].queryset.reverse())
            return super().post(request, *args, **kwargs)


class CommentUpdateView(CommentBaseMixin, UpdateView):
    """Comment更新画面"""
    template_name = 'comment_create.html'
    model = Comment
    form_class = CommentCreateForm


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Comment作成画面"""
    template_name = 'comment_create.html'
    model = Comment
    form_class = CommentCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:group_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(TroubleGroup, pk=self.kwargs.get('pk'))
        context['form'] = CommentCreateForm(initial={
            'posted_group': group,
            'user': self.request.user,
        })
        return context

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
            form = CommentCreateForm(self.request.POST)
#            form.fields['attachments'].queryset = Attachment.objects.all().order_by('id')
#            print(self.request.POST)
#            print(form.fields['attachments'].queryset.reverse())
            return super().post(request, *args, **kwargs)


class SupplyItemListView(ListView):
    """消耗品List画面"""
    template_name = 'supply_item_list.html'
    model = SupplyItem
    paginate_by = 10

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        if q_word:
            object_list = SupplyItem.objects.filter(
                Q(serial_number__icontains=q_word)
                | Q(installed_device__name__icontains=q_word)
                | Q(supplytype__name__icontains=q_word)
            ).order_by('-order_date')
        else:
            object_list = SupplyItem.objects.all().order_by('-order_date')
        return object_list


class SupplyItemCreateView(LoginRequiredMixin, CreateView):
    """SupplyItem作成画面"""
    template_name = 'supply_item_create.html'
    model = SupplyItem
    form_class = SupplyItemCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:supply_item_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('supplytype'):
            supplytype = get_object_or_404(SupplyType, pk=self.request.GET.get('supplytype'))
            context['form'] = SupplyItemCreateForm(initial={
                'supplytype': supplytype,
            })
        return context


class SupplyItemStockView(LoginRequiredMixin, CreateView):
    """SupplyItem納品登録画面"""
    template_name = 'supply_item_create.html'
    model = SupplyItem
    form_class = SupplyItemCreateForm

    def get(self, request, *args, **kwargs):
        if self.request.GET.get('supplytype'):
            supplytype = get_object_or_404(SupplyType, pk=self.request.GET.get('supplytype'))
            item = SupplyItem.objects.all().filter(supplytype=supplytype, stock_date=None).first()
            if item:
                return redirect(f'../supply_item_update/{item.id}/?operation=stock')
            else:
                return super().get(request, **kwargs)
        else:
            return super().get(request, **kwargs)


class SupplyItemExchangeView(LoginRequiredMixin, UpdateView):
    """SupplyItem使用開始画面"""
    template_name = 'supply_item_exchange.html'
    model = SupplyItem
    form_class = SupplyItemExchangeForm

    def get_success_url(self):
        return reverse_lazy('ptop:supply_item_detail', kwargs={'pk': self.request.POST['next_item']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(SupplyItem, pk=self.kwargs.get('pk'))
        context['item'] = item
        context['form'] = SupplyItemExchangeForm(initial={
            'installed_device': None,
            'next_device': item.installed_device,
        })
        context['form'].fields['storage'].queryset = item.supplytype.candidate_storage
        context['form'].fields['next_item'].queryset = SupplyItem.objects.filter(supplytype=item.supplytype).filter(is_available=True)
#        print(context['previous_record'])
        return context

    def post(self, request, *args, **kwargs):
        next_item = get_object_or_404(SupplyItem, pk=self.request.POST['next_item'])
        device = get_object_or_404(Device, pk=self.request.POST['next_device'])
        date = timezone.make_aware(parse_datetime(self.request.POST['uninstall_date']))
        level = float(self.request.POST['measured_level'])
        print(next_item, date, level)
        next_item.install_date = date
        next_item.installed_device = device
        next_item.storage = None
        next_item.is_installed = True
        next_item.is_available = False
        next_item.save()
        print(f"next_item={next_item}")
        first_record = SupplyRecord(item=next_item, device=device, level=level, date=date)
        print(first_record)
        first_record.save()
        return super().post(request, *args, **kwargs)


class SupplyItemUpdateView(LoginRequiredMixin, UpdateView):
    """SupplyItem一般更新画面"""
    template_name = 'supply_item_create.html'
    model = SupplyItem
    form_class = SupplyItemUpdateForm

    def get_success_url(self):
        return reverse_lazy('ptop:supply_item_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(SupplyItem, pk=self.kwargs.get('pk'))
        if self.request.GET.get('operation') == 'stock':
            context['form'] = SupplyItemStockForm(initial={
                'supplytype': item.supplytype,
                'serial_number': item.serial_number,
                'order_date': item.order_date,
                'due_date': item.due_date,
            })
            context['form'].fields['storage'].queryset = item.supplytype.candidate_storage
        return context


class SupplyItemDetailView(LoginRequiredMixin, DetailView):
    """SupplyItem詳細画面"""
    template_name = 'supply_item_detail.html'
    model = SupplyItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(SupplyItem, pk=self.kwargs.get('pk'))
        qs = item.supplyrecord_set.all().order_by('date')
        context['record_list'] = qs

#        print(context['previous_record'])
        if qs:
            df = read_frame(qs)
            df['days'] = (df['date'] - df.at[0, 'date']) / timedelta(days=1)
            print(df)
            plt.clf()
            ax1 = plt.subplot(111)
            ax2 = ax1.twiny()

            exp_date = item.estimated_expire_date()
            if exp_date is None:
                exp_date = df.iloc[-1]['date'] + timedelta(days=1)

            exp_days = (exp_date - df.iloc[0]['date']) / timedelta(days=1)
            (a, b) = item.calc_slope(qs)
            x2 = np.linspace(df.iloc[0]['days'], exp_days + 1, 100)
            y2 = a * x2 + b
            # print(x2,y2)
            df.plot(ax=ax1, x='date', y='level', style='bo', label='record')
            if a != 0.0:
                ax2.plot(x2, y2, 'b--', label='fit')
                ax1.axvline(exp_date, c='red', ls='dashed')
        #        ax2.set_xlim(df.iloc[0]['days'], df.iloc[-1]['days'])
                ax2.set_xlim(df.iloc[0]['days'], exp_days + 1)
    #        ax1.set_xlim(df.iloc[0]['date'], df.iloc[-1]['date'])
            print(df.iloc[0]['date'], exp_date + timedelta(days=1))
            ax1.set_xlim(df.iloc[0]['date'], exp_date + timedelta(days=1))
    #        print(df_event.loc[:,'num_acc':'num_bld'])
            ax2.text(0, item.supplytype.exchange_level * 1.05, 'exchange', c='red')
            ax1.axhline(item.supplytype.exchange_level, c='red', ls='dashed')
            ax1.set_xlabel('Date')
            ax2.set_xlabel('Days from install')
            ax1.set_ylabel(f'Remaining level [{item.supplytype.level_unit}]')
            plt.ylim(0, max(item.supplytype.fault_level, item.supplytype.initial_level))
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc=0)
            ax1.get_legend().remove()

            buffer = io.BytesIO()
            plt.savefig(buffer, dpi=100, bbox_inches='tight', format='png')
            image_png = buffer.getvalue()
            graph = base64.b64encode(image_png)
            graph = graph.decode('utf-8')
            buffer.close()
            context['graph'] = graph
        return context


class SupplyRecordCreateView(LoginRequiredMixin, CreateView):
    """SupplyRecord作成画面"""
    template_name = 'supply_record_create.html'
    model = SupplyRecord
    form_class = SupplyRecordCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:supply_item_detail', kwargs={'pk': self.object.item.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplyitem = get_object_or_404(SupplyItem, pk=self.request.GET.get('supplyitem'))
        context['type'] = supplyitem.supplytype.name
        context['item'] = supplyitem.serial_number
        context['device'] = supplyitem.installed_device
        context['form'] = SupplyRecordCreateForm(initial={
            'item': supplyitem,
            'device': supplyitem.installed_device,
        })
        context['previous_record'] = supplyitem.supplyrecord_set.all().order_by('-date').first()
        print(context['item'])
        return context


class SupplyRecordUpdateView(LoginRequiredMixin, UpdateView):
    """SupplyRecord更新画面"""
    template_name = 'supply_record_create.html'
    model = SupplyRecord
    form_class = SupplyRecordCreateForm

    def get_success_url(self):
        return reverse_lazy('ptop:supply_item_detail', kwargs={'pk': self.object.item.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplyrecord = get_object_or_404(SupplyRecord, pk=self.kwargs.get('pk'))
        context['type'] = supplyrecord.item.supplytype.name
        context['item'] = supplyrecord.item.serial_number
        context['device'] = supplyrecord.item.installed_device.name
        context['form'] = SupplyRecordCreateForm(initial={
            'item': supplyrecord.item,
            'device': supplyrecord.device,
            'level': supplyrecord.level,
            'date': supplyrecord.date,
        })
        context['previous_record'] = supplyrecord.item.supplyrecord_set.all().order_by('-date').first()
        print(context['item'])
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
    elif event.group:
        m = re.match('(/\d+/)', event.group.path)
        path_root = m.group(1)
        object_list = TroubleGroup.objects.filter(
            Q(path__startswith=path_root)
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
        {'event': event, 'object_list': object_list, 'group': group}
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
    # 初発日時より前に発生したイベントがあれば初発日時を書き換える
    if group is not None:
        # groupの割当解除した時Noneになるので判定する
        if group.first_datetime is None or event.start_time < group.first_datetime:
            group.first_datetime = event.start_time
            group.save()
        return HttpResponseRedirect(reverse_lazy('ptop:group_detail', kwargs={'pk': group.pk}))
    else:
        return HttpResponseRedirect(reverse_lazy('ptop:home'))


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
        s = pd.Series([0] * len(df.columns), index=df.columns, name=start_datetime)
        df = df.append(s)
        s = pd.Series([0] * len(df.columns), index=df.columns, name=end_datetime)
        df = df.append(s)
    else:
        first_index = df.index.array[0]
        last_index = df.index.array[-1]
        print("test")
        if first_index != start_datetime_trunc:
            s = pd.Series([0] * len(df.columns), index=df.columns, name=start_datetime_trunc)
            df = df.append(s)
        if last_index != end_datetime_trunc:
            s = pd.Series([0] * len(df.columns), index=df.columns, name=end_datetime_trunc)
            df = df.append(s)
    print(df)
#    df = df.sort_index().asfreq(freq_str, fill_value=0).fillna(0)
    df = df.sort_index().asfreq(freq_str, fill_value=0).fillna(0)
    print(df)
    return df


def draw_availability(df, interval):
    print(interval)
    df = df[:-1]
    df.index = pd.to_datetime(df.index)
    plt.clf()
    ax1 = plt.subplot(111)
    df.plot(ax=ax1, y='treatment_availability', style='ro-', label='')
    print(df.index)
    plt.ylabel('Machine Availability for Treatment')
    if interval == 'month':
        plt.xlabel('Month')
        plt.xticks(df.index.to_list(), df.index.strftime('%Y\n%m').to_list(), rotation=0)
#        ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y\n%m'))
    elif interval == 'week':
        plt.xlabel('Week')
        plt.xticks(df.index.to_list(), df.index.strftime('%m/%d').to_list(), rotation=0)
#        ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m/%d'))
    elif interval == 'day':
        plt.xlabel('Day')
        plt.xticks(df.index.to_list(), df.index.strftime('%m/%d\n%a').to_list(), rotation=0)
    ax1.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    ax1.get_legend().remove()

    buffer = io.BytesIO()
    plt.savefig(buffer, dpi=100, bbox_inches='tight', format='png')
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


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
                Q(start_time__gt=start_t) & Q(start_time__lt=end_t)
            ).order_by('start_time')
            operations = Operation.objects.filter(
                ~Q(operation_type__name__iexact='装置停止')
                & Q(start_time__gt=start_t) & Q(end_time__lt=end_t)
            ).order_by('start_time')
        else:
            events = TroubleEvent.objects.all()
            operations = Operation.objects.all()

        tz_jp = pytz.timezone('Asia/Tokyo')
        start_datetime = timezone.datetime.strptime(start, '%Y-%m-%d')
        start_localized = tz_jp.localize(start_datetime)
        end_datetime = timezone.datetime.strptime(end, '%Y-%m-%d')
        end_localized = tz_jp.localize(end_datetime)
#        print(events.count())
#        print(events)
        # troubleevent
        statistics_event = events.annotate(index=Trunc('start_time', kind=subtotal_frequency)) \
            .values('index') \
            .annotate(num_event=Count('id')) \
            .annotate(subtotal_downtime=Sum('downtime')) \
            .annotate(subtotal_delaytime=Sum('delaytime')) \
            .order_by('index')
        print('annotate kasokuki')
#        statistics_event = statistics_event.filter(device__section__super_section__name='加速器').annotate(num_acc=Count('id'))
#        statistics_event = statistics_event.filter(device__section__super_section__name='照射系').annotate(num_irr=Count('id'))
#        statistics_event = statistics_event.filter(device__section__super_section__name='治療計画').annotate(num_tps=Count('id'))
#        statistics_event = statistics_event.filter(device__section__super_section__name='建屋').annotate(num_bld=Count('id'))
        print(statistics_event)
        df_event = make_dataframe(statistics_event, start_localized, end_localized, subtotal_frequency)
        # print(df_event['num_acc'],df_event['num_irr'])
        # trouble statistics(section)
        for section in Section.objects.all():
            print(section.name, events.filter(device__section=section).count())

        # trouble statistics(supersection)
        keys = []
        values = []
        for s_section in ['加速器', '照射系', '治療計画', '建屋', '不明']:
            print(s_section)
            keys.append(s_section)
            values.append(events.filter(device__section__super_section__name=s_section).count())
        dict_ss = {
            'count': values,
        }
        keys = ['Accelerator', 'Irradiation', 'TPS', 'Building', 'Other']
        df_ss = pd.DataFrame(dict_ss, index=keys)

        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                return '{p:.1f}%  ({v:d})'.format(p=pct, v=val)
            return my_autopct

        print(df_ss)
        plt.clf()
        ax1 = plt.subplot(111)
#        print(df_event.loc[:,'num_acc':'num_bld'])
        df_ss.plot.pie(ax=ax1, subplots=True, autopct=make_autopct(values), startangle=0, counterclock=False)
#        df_event.plot.bar(y=['num_acc', 'num_irr', 'num_tps', 'num_bld'], stacked=True)
        ax1.get_legend().remove()

        buffer = io.BytesIO()
        plt.savefig(buffer, dpi=100, bbox_inches='tight', format='png')
        image_png = buffer.getvalue()
        graph_ss = base64.b64encode(image_png)
        graph_ss = graph_ss.decode('utf-8')
        buffer.close()

        # operation
        statistics_operation = operations.annotate(index=Trunc('start_time', kind=subtotal_frequency)) \
            .values('index') \
            .annotate(subtotal_operation_time=Sum('operation_time')) \
            .annotate(subtotal_treatment_time=Sum('operation_time', filter=Q(operation_type__meta_type__name__iexact='治療'))) \
            .annotate(subtotal_num_treat_hc1=Sum('num_treat_hc1')) \
            .annotate(subtotal_num_treat_gc2=Sum('num_treat_gc2')) \
            .annotate(subtotal_num_qa_hc1=Sum('num_qa_hc1')) \
            .annotate(subtotal_num_qa_gc2=Sum('num_qa_gc2')) \
            .order_by('index')
        df_operation = make_dataframe(statistics_operation, start_localized, end_localized, subtotal_frequency)
        df_operation['subtotal_num_treat_all'] = df_operation['subtotal_num_treat_hc1'] + df_operation['subtotal_num_treat_gc2']
        df_operation['subtotal_num_qa_all'] = df_operation['subtotal_num_qa_hc1'] + df_operation['subtotal_num_qa_gc2']

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
#       total_downtime = events.aggregate(value=Sum('downtime'))
#       operations_annotate = operations.annotate(time_diff=(ExpressionWrapper(F('end_time')-F('start_time'), output_field=DurationField())))
        # print(operations_annotate)
#        total_operation_time = operations_annotate.aggregate(value=Sum('operation_time'))
#        s_summary['total_availability'] = 1.0 - (s_summary['subtotal_downtime'].divide(s_summary['subtotal_operation_time']))
#        s_summary['treatment_availability'] = 1.0 - (s_summary['subtotal_delaytime'].divide(s_summary['subtotal_treatment_time']))
        print(df)

        graph_avail = draw_availability(df, subtotal_frequency)

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
                    'form': form,
                    'subtotal_frequency': subtotal_frequency,
                    'df': df,
                    's_summary': s_summary,
                    'graph_ss': graph_ss,
                    'graph_avail': graph_avail,
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
                'form': form,
                'total_downtime': 0,
                'total_operation_time': 0,
                'total_availability': 0.0,
            }
        )


def trouble_statistics_create_view(request):
    form = StatisticsForm()
# 仮処置
    return 0

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

        # operation
        statistics_operation = operations.annotate(index=Trunc('start_time', kind=subtotal_frequency)) \
            .values('index') \
            .annotate(subtotal_operation_time=Sum('operation_time')) \
            .annotate(subtotal_treatment_time=Sum('operation_time', filter=Q(operation_type__meta_type__name__iexact='治療'))) \
            .annotate(subtotal_num_treat_hc1=Sum('num_treat_hc1')) \
            .annotate(subtotal_num_treat_gc2=Sum('num_treat_gc2')) \
            .annotate(subtotal_num_qa_hc1=Sum('num_qa_hc1')) \
            .annotate(subtotal_num_qa_gc2=Sum('num_qa_gc2')) \
            .order_by('index')
        df_operation = make_dataframe(statistics_operation, start_localized, end_localized, subtotal_frequency)
        df_operation['subtotal_num_treat_all'] = df_operation['subtotal_num_treat_hc1'] + df_operation['subtotal_num_treat_gc2']
        df_operation['subtotal_num_qa_all'] = df_operation['subtotal_num_qa_hc1'] + df_operation['subtotal_num_qa_gc2']

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
                    'form': form,
                    'subtotal_frequency': subtotal_frequency,
                    'df': df,
                    's_summary': s_summary,
                }
            )
    else:
        return render(
            request,
            'statistics_create.html',
            {
                'form': form,
                'total_downtime': 0,
                'total_operation_time': 0,
                'total_availability': 0.0,
            }
        )


class UnapprovedEventListView(ListView):
    """未承認イベント一覧画面"""
    model = TroubleEvent
    template_name = "unapproved_event_list.html"

    def get_queryset(self):
        object_list = TroubleEvent.objects.filter(Q(approval_operator=None))
        return object_list

    def post(self, request, *args, **kwargs):
        """post時に呼ばれる関数"""
        update_object_list = TroubleEvent.objects.filter(Q(approval_operator=None) & ~Q(group=None))
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
        context['updated_event_list'] = TroubleEvent.objects.exclude(modified_on=F('created_on')).order_by('modified_on').reverse()[:5]
        context['updated_group_list'] = TroubleGroup.objects.exclude(modified_on=F('created_on')).order_by('modified_on').reverse()[:5]
        context['supply_type_list'] = SupplyType.objects.all()
        context['instelled_supply_list'] = SupplyItem.objects.filter(is_installed=True).order_by('installed_device')
        print(context['instelled_supply_list'])
        return context

    def get_queryset(self):
        object_list = TroubleEvent.objects.order_by('start_time').reverse()[:5]
        # return render(request, 'home.html', {'current_operation':current_operation})
        return object_list
