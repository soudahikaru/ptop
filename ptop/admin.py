from .models import TroubleEvent
from .models import TroubleGroup
from .models import Operator
from .models import User
from .models import Device
from .models import Error
from django.contrib.auth.models import Group
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

#@admin.register(User)

class AdminUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('last_name', 'first_name', 'phs_number', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'last_name', 'first_name')
    search_fields = ('username', 'last_name', 'first_name', 'email')
    filter_horizontal = ('groups', 'user_permissions')

class DeviceResource(resources.ModelResource):
    class Meta:
        model = Device
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('device_id', 'name')

class DeviceAdmin(ImportExportModelAdmin):
	resource_class = DeviceResource

class ErrorResource(resources.ModelResource):
    class Meta:
        model = Error
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('error_code','error_description')

class ErrorAdmin(ImportExportModelAdmin):
	resource_class = ErrorResource


# Register your models here.
admin.site.register(User,AdminUserAdmin)
admin.site.register(TroubleGroup)
admin.site.register(TroubleEvent)
admin.site.register(Device,DeviceAdmin)
admin.site.register(Error,ErrorAdmin)
