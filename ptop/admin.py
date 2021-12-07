""" PTOP admin setting """

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import TroubleEvent
from .models import TroubleGroup
from .models import Attachment
from .models import User
from .models import Device
from .models import Error
from .models import Operation
from .models import OperationType
from .models import OperationMetaType
from .models import Comment
from .models import CommentType
from .models import CauseType
from .models import VendorStatusType
from .models import HandlingStatusType
from .models import RequireType
from .models import Section
from .models import SuperSection
from .models import DeviceType
from .models import Announcement
from .models import EffectScope
from .models import TreatmentStatusType
from .models import Urgency
from .models import TroubleCommunicationSheet
from .models import EmailAddress
from .models import Room, Storage
from .models import SupplyType, SupplyItem, SupplyRecord
from .models import Reminder, ReminderType

# @admin.register(User)


class AdminUserAdmin(UserAdmin):
    """ user admin class """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('last_name', 'first_name', 'phs_number', 'email', 'is_tcs_destination', 'display_order')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'last_name', 'first_name', 'display_order')
    search_fields = ('username', 'last_name', 'first_name', 'email')
    filter_horizontal = ('groups', 'user_permissions')


class DeviceResource(resources.ModelResource):
    """ Resource for Device model """
    class Meta:
        """ Resource for Device model Meta"""
        model = Device
        skip_unchanged = True
        report_skipped = False


class DeviceAdmin(ImportExportModelAdmin):
    """ Admin for Device model """
    resource_class = DeviceResource


class ErrorResource(resources.ModelResource):
    """ Resource for Error model """
    class Meta:
        """ Resource for Error model Meta"""
        model = Error
        skip_unchanged = True
        report_skipped = False


class ErrorAdmin(ImportExportModelAdmin):
    """ Admin for Error model """
    resource_class = ErrorResource


class OperationTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = OperationType
        skip_unchanged = True
        report_skipped = False


class OperationTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = OperationTypeResource


class OperationMetaTypeResource(resources.ModelResource):
    """ Resource for Operation Meta Type """
    class Meta:
        """ Resource for Operation Meta Type Meta"""
        model = OperationMetaType
        skip_unchanged = True
        report_skipped = False


class OperationMetaTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = OperationMetaTypeResource


class CommentTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = CommentType
        skip_unchanged = True
        report_skipped = False


class CommentTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = CommentTypeResource


class CauseTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = CauseType
        skip_unchanged = True
        report_skipped = False


class CauseTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = CauseTypeResource


class VendorStatusTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = VendorStatusType
        skip_unchanged = True
        report_skipped = False


class VendorStatusTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = VendorStatusTypeResource


class HandlingStatusTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = HandlingStatusType
        skip_unchanged = True
        report_skipped = False


class HandlingStatusTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = HandlingStatusTypeResource


class RequireTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = RequireType
        skip_unchanged = True
        report_skipped = False


class RequireTypeAdmin(ImportExportModelAdmin):
    """ Admin for Require_items """
    resource_class = RequireTypeResource


class SectionResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = Section
        skip_unchanged = True
        report_skipped = False


class SectionAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = SectionResource


class SuperSectionResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = SuperSection
        skip_unchanged = True
        report_skipped = False


class SuperSectionAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = SuperSectionResource


class DeviceTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = DeviceType
        skip_unchanged = True
        report_skipped = False


class DeviceTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = DeviceTypeResource


class TreatmentStatusTypeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = TreatmentStatusType
        skip_unchanged = True
        report_skipped = False


class TreatmentStatusTypeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = TreatmentStatusTypeResource


class EffectScopeResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = EffectScope
        skip_unchanged = True
        report_skipped = False


class EffectScopeAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = EffectScopeResource


class UrgencyResource(resources.ModelResource):
    """ Resource for Operation Type """
    class Meta:
        """ Resource for Operation Type model Meta"""
        model = Urgency
        skip_unchanged = True
        report_skipped = False


class UrgencyAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = UrgencyResource


class SupplyRecordResource(resources.ModelResource):
    """ Resource for SupplyRecord """
    class Meta:
        """ Resource for SupplyRecord model Meta"""
        model = SupplyRecord
        skip_unchanged = True
        report_skipped = False


class SupplyRecordAdmin(ImportExportModelAdmin):
    """ Admin for Operation Type """
    resource_class = SupplyRecordResource


# Register your models here.
admin.site.register(User, AdminUserAdmin)
admin.site.register(Attachment)
admin.site.register(Announcement)
admin.site.register(TroubleGroup, SimpleHistoryAdmin)
admin.site.register(TroubleEvent, SimpleHistoryAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(EmailAddress)
admin.site.register(CauseType, CauseTypeAdmin)
admin.site.register(RequireType, RequireTypeAdmin)
admin.site.register(VendorStatusType, VendorStatusTypeAdmin)
admin.site.register(HandlingStatusType, HandlingStatusTypeAdmin)
admin.site.register(Operation)
admin.site.register(OperationType, OperationTypeAdmin)
admin.site.register(OperationMetaType, OperationMetaTypeAdmin)
admin.site.register(Comment)
admin.site.register(TroubleCommunicationSheet)
admin.site.register(CommentType, CommentTypeAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(SuperSection, SuperSectionAdmin)
admin.site.register(DeviceType, DeviceTypeAdmin)
admin.site.register(EffectScope, EffectScopeAdmin)
admin.site.register(TreatmentStatusType, TreatmentStatusTypeAdmin)
admin.site.register(Urgency, UrgencyAdmin)
admin.site.register(Room)
admin.site.register(Storage)
admin.site.register(SupplyType)
admin.site.register(SupplyItem)
admin.site.register(SupplyRecord, SupplyRecordAdmin)
admin.site.register(Reminder)
admin.site.register(ReminderType)
