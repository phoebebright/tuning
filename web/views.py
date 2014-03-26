
#django
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse,HttpResponseRedirect, Http404
from django.template.context import RequestContext
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.template.base import TemplateDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.forms.models import BaseInlineFormSet


from django.core.urlresolvers import reverse

from django.template import loader, Context
from django.views.generic import ListView
from django.views.generic.base import View
from django.forms.models import modelformset_factory
from django.forms.models import inlineformset_factory

#python
from datetime import datetime, timedelta, date


from django.conf import settings

from web.models import *


def dashboard(request):

    # TODO: Only admins

    return render_to_response('dashboard.html',{
        'bookings':Booking.objects.current(),
       },
    context_instance=RequestContext(request)
    )