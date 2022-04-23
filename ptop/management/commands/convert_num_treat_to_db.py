""" PT-DOM batch command """

# 治療人数をハードコーディングからDBのOperationResultに移すバッチ処理

from django.core.management.base import BaseCommand
from ptop.models import BeamCourse, OperationResult
from ptop.models import Operation, OperationType


class Command(BaseCommand):
    def add_arguments(self, parser):
        # コマンドライン引数を指定
        parser.add_argument('--commit', action='store_true')

    def handle(self, *args, **options):
        error_count = 0
        convert_count = 0
        try:
            print(options['commit'])
            is_committed = options['commit']
            queryset = Operation.objects.all()
            operation_treat_id = OperationType.objects.filter(name__iexact='治療')[0]
            operation_pqa_id = OperationType.objects.filter(name__iexact='患者QA')[0]
            for item in queryset:
                print(item.operation_type)
                course_hc1 = BeamCourse.objects.filter(course_id__iexact='HC1')
                course_gc2 = BeamCourse.objects.filter(course_id__iexact='GC2')
#                print(course_hc1)
                if item.num_treat_hc1 and course_hc1:
                    if item.operation_type.name != '治療':
                        print(f'Operation {item.id}:運転タイプ{item.operation_type.name}が治療ではないのにnum_treat_hc1が1以上の値になっています。')
                        error_count += 1
                    result = OperationResult(
                        operation=item,
                        operation_type=operation_treat_id,
                        beam_course=course_hc1[0],
                        num_complete=item.num_treat_hc1,
                    )
                    convert_count += 1
                    print(result)
                    if is_committed:
                        result.save()
                        item.num_treat_hc1 = 0
                        item.save()
                if item.num_treat_gc2 and course_gc2:
                    if item.operation_type.name != '治療':
                        print(f'Operation {item.id}:運転タイプ{item.operation_type.name}が治療ではないのにnum_treat_gc2が1以上の値になっています。')
                        error_count += 1
                    result = OperationResult(
                        operation=item,
                        operation_type=operation_treat_id,
                        beam_course=course_gc2[0],
                        num_complete=item.num_treat_gc2,
                    )
                    convert_count += 1
                    print(result)
                    if is_committed:
                        result.save()
                        item.num_treat_gc2 = 0
                        item.save()
                if item.num_qa_hc1 and course_hc1:
                    if item.operation_type.name != '患者QA':
                        print(f'Operation {item.id}:運転タイプ{item.operation_type.name}が患者QAではないのにnum_qa_hc1が1以上の値になっています。')
                        error_count += 1
                    result = OperationResult(
                        operation=item,
                        operation_type=operation_pqa_id,
                        beam_course=course_hc1[0],
                        num_complete=item.num_qa_hc1,
                    )
                    convert_count += 1
                    print(result)
                    if is_committed:
                        result.save()
                        item.num_qa_hc1 = 0
                        item.save()
                if item.num_qa_gc2 and course_gc2:
                    if item.operation_type.name != '患者QA':
                        print(f'Operation {item.id}:運転タイプ{item.operation_type.name}が患者QAではないのにnum_qa_gc2が1以上の値になっています。')
                        error_count += 1
                    result = OperationResult(
                        operation=item,
                        operation_type=operation_pqa_id,
                        beam_course=course_gc2[0],
                        num_complete=item.num_qa_gc2,
                    )
                    convert_count += 1
                    print(result)
                    if is_committed:
                        result.save()
                        item.num_qa_gc2 = 0
                        item.save()
            print(f'変換カウント数:{convert_count}')
            print(f'エラーカウント数:{error_count}')


        except Exception as e:
            print(e)
