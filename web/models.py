import uuid
from datetime import datetime, date, timedelta, time

from django.db import models
from django.contrib.auth.models import  AbstractUser
from django.contrib.auth.models import UserManager
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.http import  Http404
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.db.models import Q
from django.forms.models import model_to_dict
from django.template import Context, Template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
from django.core.validators import  MinValueValidator



from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from model_utils.managers import QueryManager, PassThroughManager

from libs.utils import make_time, is_list
from web.exceptions import *

from django_google_maps import fields as map_fields



# faketime allows the actual date to be set in the future past - for testing can be useful
from libs.faketime import now
NOW = now()
TODAY = NOW.date()
YESTERDAY = TODAY - timedelta(days = 1)
TOMORROW = TODAY + timedelta(days = 1)

BOOKING_REQUESTED = "1"
BOOKING_BOOKED = "3"
BOOKING_COMPLETE = "5"
BOOKING_ARCHIVED = "9"

# default booking request times

def default_start():
    return datetime.combine(TOMORROW, time(12, 00))

def default_end():
   return datetime.combine(TOMORROW, time(12, 30))

class OrgQuerySet(QuerySet):

    def active(self):
        return self.filter(active=True)

class Organisation(models.Model):
    ''' organisations are the top level for both clients (studios) and providers (tuners)
    Even though most tuners are one man (yes man) band, organisation holds the
    invoice details etc.  the company end.
    The individuals are help in CustomUser
    '''

    name = models.CharField(_('Company Name (that appears on invoices)'), max_length=50)
    test = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

    @property
    def is_test(self):
        return self.test

class Client(Organisation):

    objects = PassThroughManager.for_queryset_class(OrgQuerySet)()

    @property
    def bookers(self):
        return Booker.objects.filter(client=self)

class Provider(Organisation):

    objects = PassThroughManager.for_queryset_class(OrgQuerySet)()

    @property
    def tuners(self):
        return Tuner.objects.filter(client=self)

class Studio(models.Model):
    name = models.CharField(max_length=20)
    client = models.ForeignKey(Client, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Studio Location")
        unique_together = ("name", "client")

class Instrument(models.Model):
    name = models.CharField(max_length=20)
    client = models.ForeignKey(Client, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Instrument")
        unique_together = ("name", "client")

class CustomUser(AbstractUser):

    land_line = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    active = models.BooleanField(default=True)



    # permissions = (
    #         ("directory_groups", "Can see and use the Groups tab on the Directory"),
    #         ("update_rates", "Can Update Barrister Rates"),
    #
    #     )



    @property
    def organisation(self):
        '''assumes a user will only be assigned to 1 client/provider
        '''
        try:
            return self.bookers.all()[0]
        except:
            return None

    @property
    def is_tuner(self):
        return False

    @property
    def is_booker(self):
        return False


class Booker(CustomUser):

    client = models.ForeignKey(Client, null=True, blank=True)

    class Meta:
        verbose_name = _("Users - Booker")

    @property
    def is_tuner(self):
        return False

    @property
    def is_booker(self):
        return True

    @property
    def is_test(self):
        ''' is a test user is attached to an organisatino that is a test org
        '''

        if self.client:
            if self.client.test:
                return True

        return False

    def request_booking(self, when=None, where=None, what=None, deadline=None, client_ref=None, comments=None):


        #TODO: may want to limit users who can create bookings

        booking = Booking.create_booking(self, when, where, what, deadline, client_ref, comments )


        return booking



class Tuner(CustomUser):

    provider = models.ForeignKey(Provider, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("Users - Tuner")

    @property
    def is_tuner(self):
        return True

    @property
    def is_booker(self):
        return False

    @property
    def is_test(self):
        ''' is a test user is attached to an organisatino that is a test org
        '''

        if self.provider:
            if self.provider.test:
                return True

        return False

    @property
    def accepted_bookings(self):

        return Booking.objects.filter(status=BOOKING_BOOKED, tuner=self)

    def accept_booking(self, booking_ref, start_time=None, duration= settings.DEFAULT_SLOT_TIME):

        booking = Booking.objects.get(ref=booking_ref)

        booking.book(self, start_time, duration)

        return booking

class BookingsQuerySet(QuerySet):

    def requested(self):
        return self.filter(status=BOOKING_REQUESTED)

    def current(self):
        return self.filter(status__lt=BOOKING_ARCHIVED)

    def archived(self):
        return self.filter(status=BOOKING_ARCHIVED)

    def mine(self, user):

        if user.is_booker:
            return self.filter(booker=user)

        elif user.is_tuner:
            return self.filter(tuner=user)

        else:
            raise InvalidQueryset

class Booking(models.Model):
    #TODO: Add geodjango: http://django-model-utils.readthedocs.org/en/latest/managers.html#passthroughmanager

    STATUS = Choices((BOOKING_REQUESTED, _('requested')),
                     (BOOKING_BOOKED, _('booked')),
                     (BOOKING_COMPLETE, _('completed')),
                     (BOOKING_ARCHIVED, _('archived')),
                     )

    ref = models.CharField(max_length=8, unique=True)
    booker = models.ForeignKey(CustomUser, related_name="booker_user")
    client = models.ForeignKey(Client, related_name="client")
    tuner = models.ForeignKey(Tuner, blank=True, null=True, related_name="tuner_user")
    status = models.CharField(choices=STATUS, default=BOOKING_REQUESTED, max_length=1)
    requested_at = models.DateTimeField(_('when requested'), blank=True, null=True)
    booked_at = models.DateTimeField(_('when booked'), blank=True, null=True)
    completed_at = models.DateTimeField(_('when completed'), blank=True, null=True)
    cancelled_at = models.DateTimeField(_('when cancelled'), blank=True, null=True)

    paid_client_at = models.DateTimeField(_('when client paid'), blank=True, null=True)
    paid_provider = models.DateTimeField(_('when tuner paid'), blank=True, null=True)

    requested_from = models.DateTimeField(_('from time'), default=default_start)
    requested_to = models.DateTimeField(_('to time'), default=default_end)
    booked_time =  models.DateTimeField(_('booked time'), blank=True, null=True)
    duration = models.PositiveSmallIntegerField(_('duration'), default = settings.DEFAULT_SLOT_TIME )

    studio = models.ForeignKey(Studio, blank=True, null=True)
    instrument = models.ForeignKey(Instrument, blank=True, null=True)

    deadline =  models.DateTimeField(_('session start'), default=default_end)
    client_ref = models.CharField(_('session reference'), max_length=20, blank=True, null=True)
    comments = models.TextField(_('comments'), blank=True, null=True)

    objects = PassThroughManager.for_queryset_class(BookingsQuerySet)()


    def __unicode__(self):
        return "%s on %s " % (self.who, self.when)

    def get_absolute_url(self):
        return reverse('booking-detail', kwargs={'pk': self.pk})


    def save(self, *args, **kwargs):

        # generate unique booking ref
        if not self.id:
            self.ref =  str(uuid.uuid4())[:8]
            print self.ref

        # change status to archived if cancelled or when fully paid
        # TODO:test
        if self.cancelled_at or (self.paid_provider and self.client_paid):
            self.status=BOOKING_ARCHIVED

        super(Booking, self).save(*args, **kwargs)




    @property
    def start_time(self):

        if self.status == BOOKING_REQUESTED:
            return self.requested_from
        else:
            return self.booked_time

    @property
    def end_time(self):

        if self.status == BOOKING_REQUESTED:
            return self.requested_to
        else:
            return self.booked_time + timedelta(seconds= self.duration*60)

    @property
    def when(self):
        return self.start_time

    @property
    def where(self):
        if self.studio:
            return self.studio.name
        else:
            return ""

    @property
    def what(self):
         if self.instrument:
            return self.instrument.name
         else:
            return ""

    @property
    def who(self):

        return "%s(%s)" % (self.client.name, self.booker.username)

    @property
    def client_paid(self):
        ''' true if client has paid for tuning
        '''
        return self.paid_client_at

    @property
    def provider_paid(self):
        ''' true if provider has been paid for tuning
        '''
        return self.paid_provider



    def cancel(self, user):
        #TODO: test
        #TODO: prevent cancellation when status is complete
        #TODO: can only be cancelled by admin or person who created
        self.cancelled_at = NOW
        self.save()


    @classmethod
    def create_booking(cls, who, when=None, where=None, what=None, deadline=None, client_ref=None, comments=None, client=None, ):


        # get start and end times for booking
        if is_list(when):
            if len(when) == 2:
                from_time = make_time(when[0])
                to_time = make_time(when[1])
            else:
                pass
                # TODO: raise error
        else:
            from_time = make_time(when, "start")
            to_time = make_time(when, "end")



        # can't bookin in the past
        # TODO: Allow bookings in the past but only as completed bookings - ie. for payments/records purposes

        if to_time < NOW:
            raise PastDateException

        # fix end time if possible

        if deadline:

            # make sure deadline is a datetime
            if not hasattr(deadline, 'hour'):
                deadline = datetime.combine(deadline, time(23, 59))

            if deadline > from_time and deadline < to_time:
                to_time = deadline
            elif deadline < from_time:
                raise DeadlineBeforeBookingException


        if not client:
            try:
                client = who.client
            except:
                pass

        #TODO: handle case where show does not have an organisation or is not a client

        booking = Booking.objects.create(booker=who,
                                         client = client,
                                         requested_from = from_time,
                                         requested_to = to_time,
                                         requested_at = NOW)

        if where:
            booking.studio = where

        if what:
            #TODO: prevent instruments not belonging to this org
            booking.instrument = what

        if deadline:
            booking.deadline = deadline
        if client_ref:
            booking.client_ref = client_ref
        if comments:
            booking.comments = comments

        booking.save()
        booking.send_request()

        return booking


    def book(self, tuner, start_time=None, duration= settings.DEFAULT_SLOT_TIME):

        # TODO: handle start_Time that is beyond deadline or within slot time
        # TODO: handle booked_time outside requested time

        if not start_time:
            start_time = self.requested_from


        self.tuner = tuner
        self.booked_time = start_time
        self.duration = duration
        self.status = BOOKING_BOOKED
        self.booked_at = NOW
        self.save()

    def send_request(self):
        # schedule email http://www.cucumbertown.com/craft/scheduling-morning-emails-with-django-and-celery/
        subject = "Can you tune for %s between %s and %s" % (self.client.name, self.start_time, self.end_time)
        message = "To Tune %s in %s for session %s starting at %s" % (self.instrument, self.studio, self.client_id, self.deadline)
        to_email = "phoebebright310@gmail.com"
        from_email = "tuning@trialflight.com"


        send_mail(subject, message, from_email, [to_email,], fail_silently=True)

