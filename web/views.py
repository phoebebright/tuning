
#django
from django.forms import ModelForm, TextInput
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse,HttpResponseRedirect, Http404
from django.template.context import RequestContext
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
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
from django.utils.translation import ugettext_lazy as _
#python
from datetime import datetime, timedelta, date


from django.conf import settings

from web.models import *

@login_required()
def bookings_list(request):
    return render_to_response('web/booking_list.html',{

       },
    context_instance=RequestContext(request)
    )

@login_required()
def dashboard(request):

    Booking.check_to_complete()
    #TODO: Write management command to clean up unused booking records


    # TODO: Only admins
    today_start = make_time(date.today(), "start")
    today_end = make_time(date.today(), "end")


    return render_to_response('index.html',{
        'new_bookings_today': Booking.objects.requested().filter(requested_at__range=( today_start, today_end)),
        'matched_today': Booking.objects.booked().filter(booked_at__range=( today_start, today_end)),
        'tunings_today': Booking.objects.completed().filter(completed_at__range=( today_start, today_end)),
        'paid_today': Booking.objects.archived().filter(archived_at__range=( today_start, today_end)),
        'requested': Booking.objects.requested(),
        'bookings':Booking.objects.current(),
       },
    context_instance=RequestContext(request)
    )

@login_required()
def calendar(request):


    return render_to_response('calendar.html',{
        'clients':Client.objects.active(),
       },
    context_instance=RequestContext(request)
    )

@login_required()
def upcoming_bookings(request):


    return render_to_response('web/booking_upcoming.html',{

       },
    context_instance=RequestContext(request)
    )

@login_required()
def assign_tuner(request):


    return render_to_response('web/booking_assign.html',{

       },
    context_instance=RequestContext(request)
    )

@login_required()
def to_completed(request):


    return render_to_response('web/booking_to_complete.html',{

       },
    context_instance=RequestContext(request)
    )

@login_required()
def to_paid(request):


    return render_to_response('web/booking_to_paid.html',{

       },
    context_instance=RequestContext(request)
    )



''' JSONise

http://chriskief.com/2013/10/29/advanced-django-class-based-views-modelforms-and-ajax-example-tutorial/
'''
#http://ccbv.co.uk

class BookingForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['client','activity', 'client_ref', 'deadline','duration', 'requested_from', 'requested_to', 'studio', 'instrument','ref']

    def __init__(self, *args, **kwargs):
            super(BookingForm, self).__init__(*args, **kwargs)
            self.fields['client'].queryset = Client.objects.active()


    # def form_valid(self, form):
    #
    #     self.object.user = self.request.user
    #
    #     return super(BookingForm, self).form_valid(form)
    #
    # def save(self, commit=True):
    #
    #         booking = super(BookingForm, self).save(commit=commit)
    #         booking.Log(self.cleaned_data['comments'])



class ClientBookingForm(BookingForm):
    client = forms.CharField(widget=forms.HiddenInput())
    ref = forms.CharField(widget=forms.HiddenInput())


    class Meta:
        model = Booking
        fields = [ 'client', 'client_ref', 'deadline','duration', 'requested_from', 'requested_to', 'studio', 'instrument']


class BookingCreate(CreateView):
    #TODO: if user is client, should make client a hidden field but it isnt



    form_class = BookingForm
    template_name = "web/booking_form.html"
    success_url = reverse_lazy('booking_add')


    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """

        # TODO:if the current user is a client, no need to ask for the client

        if self.request.user.is_booker:
            self.form_class = ClientBookingForm
        else:
            self.form_class = BookingForm


        return self.form_class

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        '''
        in order to add comments on the form, the booking must already exist, so create a booking now with
        a temporary ref.
        '''
        new = Booking.objects.create(ref = Booking.create_temp_ref())

        form =  form_class(**self.get_form_kwargs())
        form.initial = {'client': self.request.user.organisation, 'user': self.request.user, 'ref': new.ref, 'activity': Activity.default_activity()}
        return form

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.booker = self.request.user
        self.object.save()

        return super(ModelFormMixin, self).form_valid(form)


class BookingUpdate(UpdateView):
    model = Booking


class BookingDelete(DeleteView):
    model = Booking
    success_url = reverse_lazy('Booking-list')

class BookingDetailView(DetailView):
    model = Booking

    def get_object(self, queryset=None):
        '''can retrieve object by id or ref
        '''
        if self.kwargs.has_key('ref'):

            try:
                obj = Booking.objects.get(ref=self.kwargs['ref'])
            except Booking.DoesNotExist:
                raise Http404(_("No Booking with ref %s" % self.kwargs['ref']))
        else:
            try:
                obj = Booking.objects.get(id=self.kwargs['pk'])
            except Booking.DoesNotExist:
                raise Http404(_("No Booking with id %s" % self.kwargs['pk']))


        return obj

class BookingCompleteView(DetailView):
    model = Booking
    template_name = "web/booking_complete.html"