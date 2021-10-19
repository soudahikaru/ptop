import re
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TroubleGroup
from .models import User

@receiver(post_save, sender=TroubleGroup)
def trouble_group_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.path:
		# pathが存在しない場合(新規作成)
		# classify idを設定
#		q = TroubleGroup.objects.filter(path__iregex=r'^/\d+/$')
#		if q.first() is not None:
#			print(q)
#			print(q.order_by('-id'))
#			max_root = q.order_by('-id')[0]
#			num_root = int(max_root.id)+1
#		else:
#			num_root = 1

		# 自分のgroup idと同じにする
		instance.classify_id = str(instance.id)

		#pathを設定
		instance.path = r'/' + str(instance.id) + r'/'
#		print(instance.path)
		instance.save()
		return
	else:
		finalpath = r'/' + str(instance.id) + r'/'
		if not instance.path.endswith(finalpath):
			# pathが存在するが、/自分のID/で終わらない場合=子groupのpath未入力の場合
			# 作成した瞬間はparent_path = instance.pathになっている
			print(instance.path)
			parent_path = instance.path
			q = TroubleGroup.objects.filter(path__exact=parent_path).exclude(id__exact=instance.id)
			if q is None:
				print('signal.py: on create_group, path exists but search result of path except itself is None')
				return
			parent = q[0]
			print(parent.num_created_child)
			parent.num_created_child += 1
			parent.save()
			instance.classify_id = parent.classify_id + '-%d' % parent.num_created_child
			instance.path = instance.path + str(instance.id) + r'/'
			print('instance.path=')
			print(instance.path)
			instance.save()
			return
		else:
			# 何もしない
			return
