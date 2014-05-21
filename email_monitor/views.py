from django.http import HttpResponse
from email_monitor.models import Monitor

def send(request):

    Monitor.send()

    return HttpResponse("Sent")

def check(request):

    Monitor.check()

    return HttpResponse("Checked")