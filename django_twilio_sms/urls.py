#-*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

from .views import sms_status_callback_view


urlpatterns = patterns("",
    url(r"^callback/sent/(?P<pk>\d+)/$", csrf_exempt(sms_status_callback_view), name="sms_status_callback"),
)
