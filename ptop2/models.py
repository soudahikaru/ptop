from django.db import models

# Create your models here.
class TroubleEvent(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField()
	device_id = models.CharField(max_length=100)
	cause = models.TextField()
	error_messages = models.TextField()
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()


	def __str__(self):
		return self.title
