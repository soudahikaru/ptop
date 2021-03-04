"""ptoproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ptop import views
from .views import TroubleEventList, TroubleEventDetail, EventCreateView, Home
from .views import UnapprovedEventListView
from .views import GroupCreateFromEventView
from .views import api_devices_get
from django.contrib import admin

admin.autodiscover()
admin.site.enable_nav_sidebar = False

app_name = 'ptop'

urlpatterns = [
    path('event/<int:pk>/', TroubleEventDetail.as_view(), name='event'),
    path('event_detail/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('trouble_communication_sheet/<int:pk>/', views.TroubleCommunicationSheetView.as_view(), name='trouble_communication_sheet'),
    path('lognote_sheet/<int:pk>/', views.LognoteSheetView.as_view(), name='lognote_sheet'),
    path('recurrent_event_create_from_event/<int:pk>/', views.RecurrentEventCreateFromEventView.as_view(), name='recurrent_event_create_from_event'),
    path('update_event/<int:pk>/', views.EventUpdateView.as_view(), name='update_event'),
    path('eventlist/', TroubleEventList.as_view(), name='eventlist'),
    path('event_advanced_search/', views.EventAdvancedSearchView.as_view(), name='event_advanced_search'),
    path('create_event/', EventCreateView.as_view(), name='create_event'),
    path('advanced_search/', views.AdvancedSearchView.as_view(), name='advanced_search'),
    path('group_list/', views.TroubleGroupListView.as_view(), name='group_list'),
    path('group_detail/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('update_group/<int:pk>/', views.GroupUpdateView.as_view(), name='update_group'),
    path('child_group_create/<int:pk>/', views.ChildGroupCreateView.as_view(), name='child_group_create'),
    path('group_create_from_event/<int:pk>/', GroupCreateFromEventView.as_view(), name='group_create_from_event'),
    path('unapproved_event_list/', UnapprovedEventListView.as_view(), name='unapproved_event_list'),
    path('event_classify/<int:pk_>/', views.event_classify, name='event_classify'),
    path('event_classify_execute/', views.event_classify_execute, name='event_classify_execute'),
    path('operation_list/', views.OperationListView.as_view(), name='operation_list'),
    path('create_operation/', views.OperationCreateView.as_view(), name='create_operation'),
    path('update_operation/<int:pk>/', views.OperationUpdateView.as_view(), name='update_operation'),
    path('change_operation/', views.change_operation, name='change_operation'),
    path('change_operation_execute/', views.change_operation_execute, name='change_operation_execute'),
    path('announcement_list', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcement_detail/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcement_create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('comment_create/<int:pk_>/', views.CommentCreateView.as_view(), name='comment_create'),
    path('statistics_create/', views.statistics_create_view, name='statistics_create'),
    path('error_autocomplete/', views.ErrorAutoComplete.as_view(), name='error_autocomplete'),
    path('device_autocomplete/', views.DeviceAutoComplete.as_view(), name='device_autocomplete'),
    path('popup_device_create/$', views.PopupDeviceCreate.as_view(), name='popup_device_create'),
    path('popup_error_create/$', views.PopupErrorCreate.as_view(), name='popup_error_create'),
    path('ajax_search_operation_from_datetime/', views.ajax_search_operation_from_datetime, name='ajax_search_operation_from_datetime'),
    path('api/devices/get/', api_devices_get, name='api_devices_get'),
    path('', Home.as_view(), name='home'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
