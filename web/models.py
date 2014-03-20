import uuid
from datetime import datetime, date, timedelta

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
from model_utils.managers import QueryManager

from libs.utils import make_time, is_list
from web.exceptions import *

from easy_maps.models import Address


# faketime allows the actual date to be set in the future past - for testing can be useful
from libs.faketime import now
NOW = now()
TODAY = NOW.date()
YESTERDAY = TODAY - timedelta(days = 1)
TOMORROW = TODAY + timedelta(days = 1)


class Organisation(models.Model):

    ORG_TYPES = Choices(  ('client', _('client')),
        ('provider', _('provider')),
        ('system', _('system')),
    )

    org_type = models.CharField(choices=ORG_TYPES, default=ORG_TYPES.client, max_length=8)
    name = models.CharField(max_length=50)
    address = models.TextField(blank=True, null=True)
    test = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    objects = models.Manager()
    clients = QueryManager(org_type='client', test=False, active=True)
    providers = QueryManager(org_type='provider', test=False, active=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Studio")



class Location(Address):
    name = models.CharField(max_length=20)
    organisation = models.ForeignKey('Organisation', null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Tuning Location")
        unique_together = ("name", "organisation")

class Instrument(models.Model):
    name = models.CharField(max_length=20)
    organisation = models.ForeignKey('Organisation', null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Instrument")
        unique_together = ("name", "organisation")

class CustomUser(AbstractUser):


    organisation = models.ForeignKey('Organisation', null=True, blank=True)
    land_line = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    active = models.BooleanField(default=True)
    #expertise = models.ManyToManyField('Expertise', blank=True, null=True)



    # permissions = (
    #         ("directory_groups", "Can see and use the Groups tab on the Directory"),
    #         ("update_rates", "Can Update Barrister Rates"),
    #
    #     )

    @property
    def is_test(self):
        ''' is a test user is attached to an organisatino that is a test org OR has test in username
        '''

        if self.organisation:
            if self.organisation.test:
                return True

        return False

    def request_booking(self, when=None, where=None, what=None, deadline=None, client_ref=None, comments=None):

        booking = Booking.create_booking(self, when, where, what, deadline, client_ref, comments )


        return booking

    def accept_booking(self, booking_id, start_time=None, duration= settings.DEFAULT_SLOT_TIME):

        booking = Booking.objects.get(id=booking_id)

        booking.book(self, start_time, duration)

    def requested_bookings(self):

        return Booking.objects.filter(status="asked")

    def accepted_bookings(self):

        return Booking.objects.filter(status="booked", provider=self)

class Booking(models.Model):
    #TODO: Add geodjango: http://django-model-utils.readthedocs.org/en/latest/managers.html#passthroughmanager

    STATUS = Choices(('asked', _('requested')),
                     ('booked', _('booked')),
                     ('cancelled', _('cancelled')),
                     ('completed', _('completed')),
                     ('paid_client', _('client has paid')),
                     ('paid_provider', _('provider has been paid')),
                     )

    ref = models.CharField(max_length=8, unique=True)
    booker = models.ForeignKey(CustomUser, related_name="booker")
    client = models.ForeignKey(Organisation, related_name="client")
    provider = models.ForeignKey(CustomUser, related_name="provider", blank=True, null=True)
    status = models.CharField(choices=STATUS, default=STATUS.asked, max_length=10)
    requested_at = models.DateTimeField(_('when requested'), blank=True, null=True)
    booked_at = models.DateTimeField(_('when booked'), blank=True, null=True)
    completed_at = models.DateTimeField(_('when completed'), blank=True, null=True)
    cancelled_at = models.DateTimeField(_('when cancelled'), blank=True, null=True)

    paid_client_at = models.DateTimeField(_('when client paid'), blank=True, null=True)
    paid_provider = models.DateTimeField(_('when tuner paid'), blank=True, null=True)

    requested_from = models.DateTimeField(_('from time'), blank=True, null=True)
    requested_to = models.DateTimeField(_('to time'), blank=True, null=True)
    booked_time =  models.DateTimeField(_('booked time'), blank=True, null=True)
    duration = models.PositiveSmallIntegerField(_('duration'), default = settings.DEFAULT_SLOT_TIME )

    location = models.ForeignKey(Location, blank=True, null=True)
    instrument = models.ForeignKey(Instrument, blank=True, null=True)

    deadline =  models.DateTimeField(_('session start'), blank=True, null=True)
    client_ref = models.CharField(_('session reference'), max_length=20, blank=True, null=True)
    comments = models.TextField(_('comments'), blank=True, null=True)


    def __unicode__(self):
        return "%s" % self.client.organisation


    def save(self, *args, **kwargs):

        # generate unique booking ref
        if not self.id:
            self.ref =  str(uuid.uuid4())[:8]
            print self.ref

        super(Booking, self).save(*args, **kwargs)

    @property
    def start_time(self):

        if self.status == "asked":
            return self.requested_from
        else:
            return self.booked_time

    @property
    def end_time(self):

        if self.status == "asked":
            return self.requested_to
        else:
            return self.booked_time + timedelta(seconds= self.duration*60)

    @classmethod
    def create_booking(cls, who, when=None, where=None, what=None, deadline=None, client_ref=None, comments=None):


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
            if deadline > from_time and deadline < to_time:
                to_time = deadline
            elif deadline < from_time:
                raise DeadlineBeforeBookingException

        booking = Booking.objects.create(booker=who,
                                         client = who.organisation,
                                         requested_from = from_time,
                                         requested_to = to_time,
                                         requested_at = NOW)

        if where:
            booking.location = where
        if what:
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


    def book(self, provider, start_time=None, duration= settings.DEFAULT_SLOT_TIME):

        # TODO: handle start_Time that is beyond deadline or within slot time
        # TODO: handle booked_time outside requested time

        if not start_time:
            start_time = self.requested_from


        self.provider = provider
        self.booked_time = start_time
        self.duration = duration
        self.status = "booked"
        self.booked_at = NOW
        self.save()

    def send_request(self):
        # schedule email http://www.cucumbertown.com/craft/scheduling-morning-emails-with-django-and-celery/
        subject = "Can you tune for %s between %s and %s" % (self.client.name, self.start_time, self.end_time)
        message = "To Tune %s in %s for session %s starting at %s" % (self.instrument, self.location, self.client_id, self.deadline)
        to_email = "phoebebright310@gmail.com"
        from_email = "tuning@trialflight.com"


        send_mail(subject, message, from_email, [to_email,], fail_silently=True)

