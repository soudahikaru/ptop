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
from django.contrib import admin
from django.urls import path, include
from .views import TroubleEventList, TroubleEventDetail, EventCreateView, Home
from .views import UnapprovedEventListView, EventClassifyView
from .views import GroupCreateFromEventView, EventClassifyView
from .views import api_devices_get
from  ptop import views

app_name = 'ptop'

urlpatterns = [
    path('event/<int:pk>/', TroubleEventDetail.as_view(), name='event'),
    path('eventlist/', TroubleEventList.as_view(), name='eventlist'),
    path('create_event/', EventCreateView.as_view(), name='create_event'),
    path('group_create_from_event/<int:pk>/', GroupCreateFromEventView.as_view(), name='group_create_from_event'),
    path('unapproved_event_list/', UnapprovedEventListView.as_view(), name='unapproved_event_list'),
    path('event_classify/<int:pk>/', views.event_classify, name='event_classify'),
    path('event_classify_execute/', views.event_classify_execute, name='event_classify_execute'),
    path('error_autocomplete/', views.ErrorAutoComplete.as_view(), name='error_autocomplete'),
    path('device_autocomplete/', views.DeviceAutoComplete.as_view(), name='device_autocomplete'),
    path('api/devices/get/', api_devices_get, name='api_devices_get'),
    path('', Home.as_view(), name='home')
]
