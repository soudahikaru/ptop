from .models import Operation

def common(request):
    current_operation = Operation.objects.order_by('start_time').last()
    return {'current_operation':current_operation}