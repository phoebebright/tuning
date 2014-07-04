
#django

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.core import serializers
from django.forms import ModelForm, TextInput
from django.forms.models import BaseInlineFormSet
from django.forms.models import inlineformset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse,HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import loader, Context
from django.template.base import TemplateDoesNotExist
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.edit import ModelFormMixin
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.utils import timezone


from django.contrib.auth import get_user_model
User = get_user_model()

#python
from datetime import datetime, timedelta, date
import json
import pytz
import arrow

from web.tasks import *
from libs.mail_utils import check_mail, send_requests
from notification import models as notification

#App
from web.models import *
from web.api import BookingsFullResource


def can_book(user):
    if user and user.is_authenticated():
        return  user.is_booker or user.is_admin

def can_view_bookings(user):

    if user and user.is_authenticated():
        return  user.is_booker or user.is_admin or user.is_tuner

def is_webmaster(user):

    if user and user.is_authenticated():
        return  user.is_superuser

@login_required
@user_passes_test(can_book)
def bookings_add(request, client_id=None, when=None):
    '''add a new booking with minimal information
    if the user is admin, they must supply a client id
    if the user is a booker, then the client is the organisation they are attached to
    deadline can be a datetime in format YYYYMMDDHHMM or a date in format YYYYMMDD or none
    the model will add default values as required.  ASSUME ANY TIME SUPPLIED IS LOCAL TIME
    '''

    # try to get client from user or raise error
    if not client_id or int(client_id) == 0:
        if request.user.is_booker:
            client = request.user.client
        else:
            if request.user.is_admin:
                raise InvalidID(message="Client ID must be supplied if admin user is creating new booking")
            else:
                raise InvalidActivity(message="User %s does not have permission to create a new booking" % request.user)
    else:
        try:
            client = Client.objects.get(id = client_id)
        except Client.DoesNotExist:
            raise InvalidID

    # parse deadline and assume in local time
    tz = pytz.timezone (settings.USER_TIME_ZONE)

    # if GETs, use these first
    #TODO: remove deadline as part of URL and use GET instead
    #TODO: this is geting called twice from JS - event propogating?
    when = None
    dline = None

    if request.GET.has_key('start'):
        when = arrow.get(request.GET['start']).datetime

    if request.GET.has_key('deadline'):
        dline = arrow.get(request.GET['deadline']).datetime

    if when:
        try:
            dline = datetime.strptime(deadline, "%Y%m%d%H%M")
            dline = tz.localize(dline)
        except:
            try:
                dline = datetime.strptime(deadline, "%Y%m%d").date
            except:
                raise InvalidData(message = "datetime passed %s did not parse" % deadline)

    # create new blank booking
    if when:
        new =  Booking.create_booking(request.user, client=client, when=when)
    else:
        new =  Booking.create_booking(request.user, client=client, deadline=dline)

    # prepare new booking for display in template
    if new.instrument:
        default_instrument = new.instrument
    else:
        default_instrument = "?"

    if new.studio:
        default_studio = new.studio
    else:
        default_studio = "?"

    if new.deadline:
        when_date = new.deadline.date()
        when_time = new.deadline.time()
    else:
        when_date = "?"
        when_time = "?"

    if new.client_ref:
        client_ref = new.client_ref
    else:
        client_ref = "?"

    if request.is_ajax():

        # use the api code to get a complete serialised version of object
        resource = BookingsFullResource()
        bundle = resource.build_bundle(request=request)
        booking = resource.obj_get(bundle, id=new.id)
        bundle = resource.build_bundle(obj=booking, request=request)


        return HttpResponse(resource.serialize(None, resource.full_dehydrate(bundle), 'application/json'), mimetype='application/json')
    else:
        return render_to_response('web/booking_new.html',{
            "object" : new,
            "default_activity" : new.activity.name_verb,
            "default_instrument" : default_instrument,
            "default_studio" : default_studio,
            "when_date" : when_date,
            "when_time" : when_time,
            "client_ref": client_ref,
            "price": new.price,
            "booker": new.booker,
            },
            context_instance=RequestContext(request)
        )

def render_booking_template(request, object, user=None):

    if not user:
        user = request.user
    if not user:
        raise PermissionDenied()

    if user.is_admin:
        template = "web/booking_editable_template.html"
    elif user.is_booker:
         template = "web/booking_editable_template_booker.html"
    elif user.is_tuner:
         template = "web/booking_editable_template_tuner.html"

    return render_to_string(template, {"object": object})



@login_required
@user_passes_test(can_view_bookings)
def bookings_list(request):
    return render_to_response('web/booking_list.html',{

    },
                              context_instance=RequestContext(request)
    )

@login_required()
def dashboard(request):

    #check_mail(request)
    send_requests(request)

    if request.user.is_admin:
        template = "index_admin.html"
    elif request.user.is_booker:
        template = "index_client.html"
    elif request.user.is_tuner:
        template = "index_tuner.html"

    return render_to_response(template,{},
        context_instance=RequestContext(request)
    )

@user_passes_test(is_webmaster)
def webmaster(request):

    users = User.objects.filter(is_active=True).order_by('-last_login')


    return render_to_response("webmaster.html",{
        'users': users,
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


def request_another_tuner(request, booking_ref):
    #TODO: pass a code to ensure this is a valid request

    booking = get_object_or_404(Booking, ref=booking_ref)
    TunerCall.request(booking)

''' JSONise

http://chriskief.com/2013/10/29/advanced-django-class-based-views-modelforms-and-ajax-example-tutorial/
'''
#http://ccbv.co.uk

class BookingForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['client','activity', 'client_ref', 'deadline','duration', 'requested_from', 'requested_to', 'studio', 'instrument','price','ref']

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
        form.initial = {'client': self.request.user.organisation,
                        'user': self.request.user,
                        'ref': new.ref,
                        'activity': new.activity,
                        'price': new.price }
        return form

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.booker = self.request.user

        # system is expecting to save a new booking but one was created above, so need to update instead
        self.object.save()

        new = Booking.objects.get(ref = self.object.ref)
        self.object.id = new.id


        return super(ModelFormMixin, self).form_valid(form)


class BookingUpdate(UpdateView):
    model = Booking


class BookingDelete(DeleteView):
    model = Booking
    success_url = reverse_lazy('Booking-list')

class BookingDetailView(DetailView):
    model = Booking

    #TODO: show a day calendar with times - for bookers all for client, for tuner all for tuner
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


def ping(request):
    ''' trigger a celery task and return OK
    used to test if all is well
    :param request:
    :return:
    '''

    celery_ping.delay()
    return HttpResponse('OK')


def check_bookings_task(request):
    ''' trigger a celery task and return OK
    used to test if all is well
    :param request:
    :return:
    '''

    check_bookings.delay()
    return HttpResponse('OK')

@login_required
@user_passes_test(is_webmaster)
def send_test_email(request):

    to = system_user()
    sender = settings.DEFAULT_FROM_EMAIL
    subject = "Mail 1 of 3 - test straight email"
    body = "test email body"

    try:
        send_mail(subject, body, sender, [to.email, ])
    except:
        print "Unable to send email directly from django"

    subject = "Mail 2 of 3 - test noitification generated email - send manually"
    notification.send(users=[to,],
                          label='test_notification')

    '''
    for email in EmailLog.objects.filter(date_sent__isnull = True, recipient = to ):
        email.send()

    subject = "Mail 3 of 3 - test noitification generated email - send via celery"
    notification.send(users=[to,],
                          label='test_notification')
    '''

    return HttpResponse('OK')


