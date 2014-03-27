
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

from django.views.generic.edit import ModelFormMixin
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

''' JSONise

http://chriskief.com/2013/10/29/advanced-django-class-based-views-modelforms-and-ajax-example-tutorial/
'''
#http://ccbv.co.uk

class BookingCreate(CreateView):
    model = Booking
    fields = [ 'client', 'requested_from', 'requested_to', 'duration', 'location', 'instrument', 'deadline', 'client_ref', 'comments']


    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.booker = self.request.user
        self.object.save()

        return super(ModelFormMixin, self).form_valid(form)


class BookingUpdate(UpdateView):
    model = Booking
    fields = ['name']

class BookingDelete(DeleteView):
    model = Booking
    success_url = reverse_lazy('Booking-list')