import re
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TroubleGroup
from .models import User

@receiver(post_save, sender=TroubleGroup)
def trouble_group_pre_save_receiver(sender, instance, *args, **kwargs):
	if not instance.path:
		# classify idを設定
		q = TroubleGroup.objects.filter(path__iregex=r'^/\d+/$')
		if q.first() is not None:
			print(q)
			print(q.order_by('-id'))
			max_root = q.order_by('-id')[0]
			num_root = int(max_root.classify_id)+1
		else:
			num_root = 1
			
		instance.classify_id = '%d' % num_root

		#pathを設定
		instance.path = r'/' + str(instance.pk) + r'/'
#		print(instance.path)
		instance.save()
		return

	finalpath = r'/' + str(instance.pk) + r'/'
	if not instance.path.endswith(finalpath):
		parent_path = instance.path
		q = TroubleGroup.objects.filter(path__exact=parent_path)
		parent = q[0]
#		print(parent.num_created_child)
		parent.num_created_child += 1
		parent.save()
		instance.classify_id = parent.classify_id + '-%d' % parent.num_created_child
		instance.path = instance.path + str(instance.pk) + r'/'
#		print(instance.path)
		instance.save()

