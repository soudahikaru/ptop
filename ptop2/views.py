from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import TroubleEvent

# Create your views here.

class TroubleEventDetail(DetailView):
	template_name = 'event.html'
	model = TroubleEvent
	
class TroubleEventList(ListView):
	template_name = 'eventlist.html'
	model = TroubleEvent
	
	