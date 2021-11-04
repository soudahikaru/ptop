from import_export import resources

from .models import Device


class DeviceResource(resources.ModelResource):
    class Meta:
        model = Device
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('device_id', 'name')
