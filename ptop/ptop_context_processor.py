from .models import Operation

def common(request):
    current_operation = Operation.objects.order_by('id').last()
    return {'current_operation':current_operation}