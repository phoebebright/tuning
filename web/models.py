import uuid
from decimal import *
import logging
import random

from datetime import datetime, date, timedelta, time


from django.conf import settings
from django.contrib.auth.models import  AbstractUser, UserManager
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import  MinValueValidator
from django.db import models
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.http import  Http404
from django.template import Context, Template
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.shortcuts import get_object_or_404

from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from model_utils.managers import QueryManager, PassThroughManager

#can't import here as end up with circular import - see email_logged.py
#from notification import models as notification
from libs.utils import make_time, is_list, add_tz
from web.exceptions import *

from django_google_maps import fields as map_fields
from django.forms.models import model_to_dict
from django_gravatar.helpers import get_gravatar_url


from django_twilio.client import twilio_client


"""
notifications:
https://github.com/tomchristie/django-ajax-messages - auto refreshing
https://github.com/AliLozano/django-messages-extends
https://github.com/scdoshi/django-notifier - build different backends for sms etc.
http://www.twilio.com/sms/pricing/gb - sending sms

"""
# celery_log = logging.getLogger('celery')


# faketime allows the actual date to be set in the future past - for testing can be useful
from libs.faketime import now
NOW = now()
TODAY = NOW.date()
YESTERDAY = TODAY - timedelta(days = 1)
TOMORROW = TODAY + timedelta(days = 1)

BOOKING_CREATING = "0"   # in the process of creating a booking
BOOKING_REQUESTED = "1"   # waiting for a tuner
BOOKING_BOOKED = "3"      # tuner has been assigned but not yet happened
BOOKING_TOCOMPLETE = "4"      # booking has past and not marked complete
BOOKING_COMPLETE = "5"    # tuning has been done but not yet paid
BOOKING_CLIENT_PAID = "6"    # client has  paid but not provider
BOOKING_PROVIDER_PAID = "7"    # provider has been paid but not client
BOOKING_CANCELLED = "8"    # tuning cancelled
BOOKING_ARCHIVED = "9"    # paid and finished

CALL_INITIALISING = 'I'
CALL_WAITING = 'W'
CALL_REJECTED = 'R'
CALL_ACCEPTED = 'A'
CALL_EXPIRED = 'E'
CALL_FAILED = 'F'

def send_notification(users, label, extra_context=None, sender=None):

    # import here to avoid circular import
    from notification import models as notification
    # if in test - always send mails but only to testers
    if settings.DEBUG:

            system = system_user()

            if not extra_context:
                extra_context = {}

            extra_context['system_info'] = "TEST MODE - email for %s" % users
            notification.send([system,], label, extra_context, sender)

    else:
        notification.send(users, label, extra_context, sender)

# default booking request times

def default_deadline(dt = None):
    """Get the default deadline time for a booking.

    :param dt: date for booking
    :return: If no dt supplied returns tomorrow at DEFAULT_DEADLINE_TIME
        otherwise, returns dt at DEFAULT_DEADLINE_TIME
    """
    if not dt:
        dt = TOMORROW

    h,m = settings.DEFAULT_DEADLINE_TIME.split(":")
    return make_time(datetime.combine(dt, time(int(h), int(m))))



def default_start(deadline = None):
    """Get default start time.

    If deadline is supplied, make it DEFAULT_SLOT_TIME mins before deadline.  If deadline not supplied, use
        default_deadline time.
    """
    if not deadline:
        deadline = default_deadline()

    return make_time( deadline - timedelta(minutes = settings.DEFAULT_SLOT_TIME))

def default_end(start = None):
    """Get default end time of booking.

    If start (datetime) is supplied, then end is DEFAULT_SLOT_TIME minutes after start
    If start not supplied, then end if DEFAULT_SLOT_TIME after default_start
    """
    if start:
        return make_time( start + timedelta(minutes = settings.DEFAULT_SLOT_TIME))
    else:
        h,m = settings.DEFAULT_DEADLINE_TIME.split(":")
        return make_time(datetime.combine(TOMORROW, time(int(h), int(m))))


def system_user():

    try:
        return CustomUser.objects.get(username='system')
    except CustomUser.DoesNotExist:
        raise NoSystemUser



def add_admins(users):
    # add admin users to list of users supplied
    for admin in CustomUser.objects.filter(username__in=settings.NOTIFICATIONS_ADMINS):
        if admin not in users:
            users += [admin]

    return users

def base_price(price, dt = None):
    if dt and dt.weekday() == 6:
        return price + sunday_extra()
    else:
        return price

def vat_rate():
    return Decimal('.21')

def short_notice_extra():
    return Decimal('20.0')

def sunday_extra():

    return Decimal('15.0')

def emergency_price(price):

    return price * Decimal('1.5')

def tuner_pay(price):
    #TODO: tuners can be vat registered
    # assume for the moment that tuners are not vat registered
    return Decimal(price) * Decimal('0.66')






class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                                           self._meta.fields])


class Activity(models.Model):
    name = models.CharField(_('name'), max_length=12, unique=True, help_text="eg Tuning")
    name_plural = models.CharField(_('plural'), max_length=15, help_text="eg. Tunings")
    name_verb = models.CharField(_('verb'), max_length=20, help_text="eg. Tune")
    name_verb_past =   models.CharField(_('verb past'), max_length=20, help_text="eg. Tuned")
    duration = models.PositiveIntegerField(_('Default time slot in minutes '), max_length=5, default=60)
    order = models.PositiveSmallIntegerField(_('Order to display in lists'), default=0)
    price = models.DecimalField(_('Default price (ex vat)'), max_digits=10, decimal_places=2, default=50)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "activities"

    @classmethod
    def default_activity(cls):
        '''returns the top of the list
        '''

        return cls.objects.all()[0]



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
    test = models.BooleanField(default=False, db_index=True)
    active = models.BooleanField(default=True, db_index=True)


    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name',]

    @property
    def is_test(self):
        return self.test

class Client(Organisation):
    #TODO: All clients need at least one booker

    objects = PassThroughManager.for_queryset_class(OrgQuerySet)()

    @property
    def bookers(self):
        return Booker.objects.filter(client=self)

    @property
    def studios(self):
        return Studio.objects.filter(client=self)

    @property
    def instruments(self):
        return Instrument.objects.filter(client=self)


    def new_booking(self):
        how = None
        where = None
        what = None
        who = None
        when = None

        how = Activity.default_activity()

        # pick first in list as default


        studios = self.studios
        if len(studios) > 0:
            where = studios[0]

        instruments = self.instruments
        if len(instruments) > 0:
            what = instruments[0]

        bookers = self.bookers
        if len(bookers) > 0:
            who = bookers[0]

        booking = Booking.create_booking(self, when=when, where=where, what=what, how=how)

        return booking

class Provider(Organisation):

    objects = PassThroughManager.for_queryset_class(OrgQuerySet)()

    @property
    def tuners(self):
        return Tuner.objects.filter(client=self)

class Studio(models.Model):
    name = models.CharField(max_length=20)
    short_code = models.CharField(max_length=3, unique=True, db_index=True)
    client = models.ForeignKey(Client, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Studio Location")
        unique_together = ("name", "client")

    @property
    def lat(self):
        return self.geolocation._split_geo_point.im_self.lat

    @property
    def lon(self):
        return self.geolocation._split_geo_point.im_self.lon

class Instrument(models.Model):
    name = models.CharField(max_length=20)
    client = models.ForeignKey(Client, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("Instrument")
        unique_together = ("name", "client")

class CustomUser(AbstractUser, ModelDiffMixin):

    land_line = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    gravatar = models.URLField(blank=True, null=True)
    use_email = models.BooleanField(default=True)
    use_sms = models.BooleanField(default=False)


    def save(self, *args, **kwargs):

        if 'email' in self.changed_fields or not self.gravatar:
            self.gravatar = get_gravatar_url(self.email, size=80)

        super(CustomUser, self).save(*args, **kwargs)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    @property
    def organisation(self):
        '''assumes a user will only be assigned to 1 client/provider
        '''
        try:
            return self.bookers.all()[0]
        except:
            return None

    @property
    def user_type(self):
        if self.is_admin:
            return "admin"
        elif self.is_booker:
            return "booker"
        elif self.is_tuner:
            return "tuner"
        else:
            return "?"

    @property
    def is_tuner(self):
        return False

    @property
    def is_booker(self):
        return False

    @property
    def is_admin(self):
        return self.is_staff

    @property
    def can_book(self):
        return self.is_staff

    @property
    def can_see_price(self):
        return self.is_staff or self.is_booker

    @property
    def client(self):
        return None


    def can_cancel(self, booking):

        if self.is_admin:
            return True
        elif self.is_booker and self.client == booking.client:
            return True

        return False

    @property
    def logfilter(self):
        ''' used in ajax call to get log messages
        '''

        # admin sees all
        if self.is_admin:
            return "{}"

        # booker sees all for this client
        if self.is_booker:
            return '{"client_id":%s}' % self.client_id

        # booker sees all for this client
        if self.is_tuner:
            return '{"user_id":%s}' % self.id

    @property
    def last_activity(self):

        items = Log.objects.filter(created_by = self).order_by('-created')
        if items:
            return items[0].created
        else:
            return None

    @classmethod
    def admin_emails(cls):

        return cls.objects.filter(is_staff=True).values_list('email')

class Booker(CustomUser):

    client = models.ForeignKey(Client, null=True, blank=True)

    class Meta:
        verbose_name = _("Users - Booker")

    @property
    def is_admin(self):
        return False

    @property
    def is_booker(self):
        return True

    @property
    def can_book(self):
        return True

    @property
    def is_test(self):
        ''' is a test user is attached to an organisatino that is a test org
        '''

        if self.client:
            if self.client.test:
                return True

        return False

    def request_booking(self, when=None, where=None, what=None, deadline=None, client_ref=None, how=None, comments=None):
        """create a booking for this user with status BOOKING_REQUESTED.
        calls Booking.create_booking with a who of this user and commit=True
        :return: new booking object
        """
        #TODO: Only used in testing I think.

        #TODO: may want to limit users who can create bookings

        booking = Booking.create_booking(self, when, where, what, deadline, client_ref, how, comments, commit=True )
        booking.status = BOOKING_REQUESTED
        booking.save()

        return booking


class Tuner(CustomUser):

    provider = models.ForeignKey(Provider, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, blank=True, null=True)
    activities = models.ManyToManyField(Activity, blank=True, null=True)
    score = models.PositiveSmallIntegerField(default=1)

    #TODO: add vat registered
    #TODO: add availability schedule


    class Meta:
        verbose_name = _("Users - Tuner")

    @property
    def is_tuner(self):
        return True

    @property
    def is_admin(self):
        return False

    @property
    def can_book(self):
        return False

    @property
    def is_contactable(self):
        return self.use_email or self.use_sms

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

        booking.set_booked(self, start_time, duration)

        return booking

    def is_available(self, booking):
        ''' check availability and ability to do a booking
        :param booking:
        :return: true/false
        '''

        #TODO: check activity
        return True


class BookingsPassThroughManager(PassThroughManager):

    def get_queryset(self):
        return super(BookingsPassThroughManager, self).get_queryset()


class BookingsQuerySet(QuerySet):


    def requested(self):
        return self.filter(status=BOOKING_REQUESTED).select_related().order_by('-requested_at')

    def booked(self):
        return self.filter(status=BOOKING_BOOKED).order_by('-booked_time')

    def completed(self):
        return self.filter(status=BOOKING_COMPLETE).order_by('-completed_at')

    def unpaid(self, user):
        # from admins perspective, unpaid is both client and provider
        if user.is_admin:
            return self.completed()

        # from bookers perspective, means they havn't paid
        if user.is_booker:
            return self.filter(status=BOOKING_COMPLETE, paid_client_at__isnull=True).order_by('-completed_at')

        # from tuners perspective, means they havn't been paid
        if user.is_tuner:
            return self.filter(status=BOOKING_COMPLETE, paid_provider_at__isnull=True).order_by('-completed_at')


    def cancelled(self):
        return self.filter(status=BOOKING_CANCELLED).order_by('-cancelled_at')

    def archived(self):
        return self.filter(status=BOOKING_ARCHIVED).order_by('-archived_at')

    def to_complete(self):
        '''booked and past start time
        '''
        return self.filter(status=BOOKING_TOCOMPLETE).order_by('-requested_to')

    def current(self):
        return self.filter(status__lt=BOOKING_CANCELLED, status__gt=0).order_by('-deadline')

    def ours(self, client):

        return self.filter(client=client)

    def mine(self, user):

        # booker can see all bookings for the client
        if user.is_booker:
            return self.filter(client=user.client)

        elif user.is_tuner:
            # all this tuners bookings and bookings looking for tuners
            return self.filter(Q(tuner=user) | Q(status=BOOKING_REQUESTED))

        elif user.is_admin:
            return self

        else:
            raise InvalidQueryset(message = "user %s must be booker, tuner or admin" % user)

class Booking(models.Model, ModelDiffMixin):
    #TODO: Add geodjango: http://django-model-utils.readthedocs.org/en/latest/managers.html#passthroughmanager

    STATUS = Choices((BOOKING_REQUESTED, _('requested')),
                     (BOOKING_BOOKED, _('booked')),
                     (BOOKING_TOCOMPLETE, _('completed?')),
                     (BOOKING_COMPLETE, _('completed')),
                     (BOOKING_CANCELLED, _('cancelled')),
                     (BOOKING_ARCHIVED, _('archived')),
                     )

    ref = models.CharField(max_length=30, unique=True)
    booker = models.ForeignKey(CustomUser, related_name="booker_user", blank=True, null=True)
    client = models.ForeignKey(Client, related_name="client")
    tuner = models.ForeignKey(Tuner, blank=True, null=True, related_name="tuner_user")
    activity = models.ForeignKey(Activity, blank=True, null=True, db_index=True)
    status = models.CharField(choices=STATUS, default=BOOKING_CREATING, max_length=1, db_index=True)
    requested_at = models.DateTimeField(_('when requested'), blank=True, null=True)
    booked_at = models.DateTimeField(_('when booked'), blank=True, null=True)
    completed_at = models.DateTimeField(_('when completed'), blank=True, null=True)
    cancelled_at = models.DateTimeField(_('when cancelled'), blank=True, null=True)
    paid_client_at = models.DateTimeField(_('when client paid'), blank=True, null=True)
    paid_provider_at = models.DateTimeField(_('when tuner paid'), blank=True, null=True)
    archived_at = models.DateTimeField(_('when archived'), blank=True, null=True)

    requested_from = models.DateTimeField(_('from time'), default=default_start, blank=True, null=True)
    requested_to = models.DateTimeField(_('to time'), default=default_end, blank=True, null=True)
    booked_time =  models.DateTimeField(_('booked time'), blank=True, null=True)
    duration = models.PositiveSmallIntegerField(_('duration'), default = settings.DEFAULT_SLOT_TIME, blank=True, null=True)

    studio = models.ForeignKey(Studio, blank=True, null=True)
    instrument = models.ForeignKey(Instrument, blank=True, null=True)

    deadline =  models.DateTimeField(_('session start'), blank=True, null=True, db_index=True)
    client_ref = models.CharField(_('session reference'), max_length=30, blank=True, null=True)

    price = models.DecimalField(_('Price for job ex vat'), max_digits=10, decimal_places=2, default=0)
    default_price = models.DecimalField(_('System calculated price for job ex vat'), max_digits=10, decimal_places=2, default=0)
    tuner_payment = models.DecimalField(_('Amount due to Tuner'), max_digits=10, decimal_places=2, default=0)
    vat = models.DecimalField(_('VAT Amount'), max_digits=10, decimal_places=2, default=vat_rate())

    request_count = models.PositiveSmallIntegerField(default=0)

    objects = BookingsPassThroughManager.for_queryset_class(BookingsQuerySet)()


    def __unicode__(self):
        return "%s %s on %s %s " % (self.ref, self.studio, self.when.strftime('%b'), self.when.strftime('%d'))

    def get_absolute_url(self):
        return reverse('booking-detail', kwargs={'pk': self.id})

    class Meta:
        ordering = ["-deadline",]


    def save(self, *args, **kwargs):

        if kwargs.has_key('user'):
            user = kwargs['user']
            kwargs.pop('user')
        else:
            user = None

        # generate unique booking ref
        if not self.id:
            if not self.ref:
                self.ref = Booking.create_ref()

            self.activity = Activity.default_activity()
            self.requested_at = now()
            self.recalc_prices(user)

        # recalculate price/vat if appropriate
        if 'price' in self.changed_fields:
            # recalc vat
            self.vat = self.default_price * vat_rate()
            self.tuner_payment = tuner_pay(self.price)
        else:
            if 'requested_at' in self.changed_fields:
                self.recalc_prices(user)

        # truncate client_ref if necessary
        if self.client_ref and len(self.client_ref) > 30:
            self.client_ref = self.client_ref[0:30]

        super(Booking, self).save(*args, **kwargs)


        # become booked once there is a tuner
        if self.status < BOOKING_BOOKED and self.tuner:
            self.set_booked(self.tuner, start_time=self.requested_from, duration= self.duration)

        # change status to archived  when fully paid
        # TODO:test
        if self.status >= BOOKING_COMPLETE and self.status < BOOKING_CANCELLED and self.paid_provider_at and self.paid_client_at:

            self.set_archived()




        return self

    def recalc_prices(self, user=None):
        #NOTE: does not save
        old_price = self.price

        self.default_price = self.get_default_price() * Decimal(str(self.duration)) / Decimal('60.00')
        self.vat = self.default_price * vat_rate()
        self.price = self.default_price
        self.tuner_payment = tuner_pay(self.price)

        # if user and old_price != self.price:
        #     add_message(user, "Price has changed!")

        return {'default_price': self.default_price,
                'vat': self.vat,
                'price': self.price,
                'tuner_payment': self.tuner_payment}

    @property
    def total(self):
        '''
        :return: price including VAT
        '''

        return self.price + self.vat

    @classmethod
    def create_ref(cls):
        # create unique 6 alphanum ref for booking
        code = str(uuid.uuid4())[:6]
        while True:
            try:
                used = Booking.objects.get(ref = code)
                code = str(uuid.uuid4())[:6]
            except Booking.DoesNotExist:
                # not found so is unique
                return code


    def is_editable(self, user=None):
        ''' used to determine if the booking can be changed in the front end
        :return:
        '''

        if not user:
            return False

        # can edit until marked as completed - otherwise will have to use admin interface
        if user.is_admin and self.status < BOOKING_COMPLETE:
            return True

        # tuners can't edit
        if user.is_tuner:
                return False

        if user.is_booker and self.status < BOOKING_COMPLETE and self.client == user.client:
            return True


        return False

    @property
    def short_heading(self):
        return self.ref

    @property
    def long_heading(self):
        return "%s (%s)" % (self.client, self.ref)

    @property
    def short_description(self):

        return "%s at %s on %s at %s" % (self.activity, self.studio, formats.date_format(self.when, "SHORT_DATE_FORMAT"), formats.time_format(self.when, "TIME_FORMAT"))

    def description_for_user(self, user):
        '''
        :param: user can be a user object or one of the following strings "admin", "booker", "tuner"
        :return:includes money
        '''

        base = self.description

        if type(user)  == type("duck"):
            user_type = user
        else:
            # assume it's a user object
            user_type = user.user_type


        if user_type == "admin":
            return "%s charging %s%s paying %s%s" % (base, "&pound;", self.price, "&pound;", self.tuner_payment)

        if user_type == "booker":
            return "%s price %s%s ex VAT" % (base, "&pound;", self.price)

        if user_type == "tuner":
            return "%s  paying %s%s" % (base, "&pound;", self.tuner_payment)



    def text_description_for_user(self, user):

        descr = self.description_for_user(user)

        # replace pound signs etc.
        #TODO: get pound sign - if put chr(156) instead of "" then get error
        #  'ascii' codec can't decode byte 0x9c in position 0: ordinal not in range(128)\n"
        descr = descr.replace("&pound;", "")

        return descr

    @property
    def description(self):
        '''
        text description of this booking
        :return:
        '''
        txt = ''

        if self.status <= BOOKING_REQUESTED:
            txt = 'Request to %s ' % self.activity.name_verb
        elif self.tuner:
            if self.status < BOOKING_COMPLETE:
                txt = "%s to %s " % (self.tuner.full_name, self.activity.name_verb)
            else:
                txt = "%s %s " % (self.tuner.full_name, self.activity.name_verb_past)
        else:
            txt = ""

        if self.instrument:
            txt += "%s " % self.instrument


        if self.studio:
            txt += "at %s " % self.studio

        txt += "starting %s " %  (formats.date_format(self.start_time, "TIME_FORMAT"), )

        if self.deadline:
            txt  += "for session starting at %s " % (formats.date_format(self.deadline, "TIME_FORMAT"), )

        if self.client_ref:
            txt += "with ref %s " % self.client_ref

        return txt

    @property
    def comments(self):
        return Log.objects.filter(booking=self)

    @property
    def start_time(self):
        ''' when booking is only requested show the whole possible slot time
        when becomes booked, show the actual time when the tuning will happen
        :return:
        '''
        if self.booked_time:
            return self.booked_time
        else:
            return self.requested_from

    @property
    def end_time(self):

        if self.booked_time:
            return self.booked_time + timedelta(seconds= self.duration*60)
        else:
            return self.requested_to



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
            return self.activity.name_verb + " " + self.instrument.name
        else:
            return self.activity.name

    @property
    def who(self):
        try:
            return "%s(%s)" % (self.client.name, self.booker.username)
        except:
            return ''

    @property
    def has_client_paid(self):
        ''' true if client has paid for tuning
        '''
        return self.paid_client_at != None

    @property
    def has_provider_paid(self):
        ''' true if provider has been paid for tuning
        '''
        return self.paid_provider_at != None

    @property
    def cancelled(self):

        return self.cancelled_at != None

    @property
    def sla_assign_tuner_by(self):
        ''' time at which sla expires
        '''
        return self.requested_at + timedelta(seconds= settings.SLA_ASSIGN_TUNER * 60)

    @property
    def sla_assign_tuner_togo(self):
        '''minutes until sla expires or 0 if already expired
        '''
        if self.sla_assign_tuner_by > NOW:
            return int((self.sla_assign_tuner_by - NOW).total_seconds() / 60)
        else:
            return 0

    @property
    def sla_assign_tuner_pct(self):
        ''' percent of sla expired
        '''
        if self.sla_assign_tuner_by > NOW:
            mins2go = int((self.sla_assign_tuner_by - NOW).total_seconds() / 60.0)
            return int((settings.SLA_ASSIGN_TUNER - mins2go) *100 / settings.SLA_ASSIGN_TUNER)

        else:
            return 100

    @property
    def calls(self):
        return TunerCall.objects.filter(booking=self).order_by('called')

    def get_default_price(self):

        price = base_price(self.activity.price, self.start_time)

        # if starts within 2 hours
        if (self.start_time - NOW).seconds < (60*60*3):
            price = emergency_price(price)

        # start within 24 hours
        elif (self.start_time - NOW).days < 1:
            price += short_notice_extra()

        return price

    def log(self, comment,  type, user=None):
        '''add a system generated item to the comments log
        '''
        if not user:
            user = system_user()

        item = Log.objects.create(booking=self, comment= comment, created_by=user, log_type=type)
        return item

    def comment(self, comment, user=None):
        '''add user generated comment to the comments log
        '''
        if not user:
            user = system_user()

        item = Log.objects.create(booking=self, comment= comment, created_by=user, log_type='U')
        return item


    def make_booking(self, user=None):
        ''' save booking and change status 1 so it becomes a real booking.  Bookings are created with cls.booking_create
        with a status of 0 so that they can be edit from javascript.  Don't become real until the user clicks on
        save and this method is called
        '''
        #TODO: some validation here
        if  int(self.status) == 0:
            self.status = BOOKING_REQUESTED
            self.booked_at = NOW
            self.save()

            # initiate calls to tuners if booking is in the future
            # just check for date as may create an urgent booking for NOW
            if not self.tuner and self.deadline.date() >= NOW.date():
                TunerCall.request(self)

            self.log("Booking Requested" , user=user, type = "REQUEST")

            # notifications - don't send if booking is past
            if self.deadline.date() >= NOW.date():

                send_notification(add_admins([self.booker,]),
                            "booking_requested",
                            {
                                "booking": self,
                                "description": self.description_for_user(self.booker)

                            })


        return self





    def request_tuner(self, call , user=None):

        if TunerCall.request(self):
            self.request_count += 1
            self.save()
            self.log("Message sent to %s" % call.tuner, user=user, type = "GET TUNER")
        else:
            #TODO: handle request failed exception
            raise RequestTunerFailed


    def cancel(self, user=None):

        # can be a string - shouldn't have to fix here!
        status = int(self.status)

        # if not created then just delete
        if status == 0:
            #TODO: delete comments
            self.delete()


        else:

            #TODO: test
            #TODO: prevent cancellation when status is complete
            #TODO: can only be cancelled by admin or person who created
            self.cancelled_at = NOW
            self.status = BOOKING_CANCELLED
            self.save()

            # canications
            msg = "Booking CANCELLED"
            self.log(comment=msg, user=user, type='CANCEL')

            # notifications - don't send if booking is past
            if self.deadline.date() >= NOW.date():

                who = [self.booker,]
                if self.tuner:
                    who += self.tuner

                send_notification(add_admins(who),
                            "booking_cancelled",
                            {
                                "booking": self,

                            })


            PhoneNumber.release(self)

    def change_all_times(self, time_type, requested):
        ''' one time is changed and adjust all other times.  Usuall this is called from the
        api, eg. a booking has been dragged on the calendar
        If changing on a form, then won't want to have this ripple effect, so just use
        change_requested_from etc.
        '''

        # once booked, can't change time
        if self.status < BOOKING_BOOKED:

            if time_type == "requested_from":

                # get difference of change and apply that to end and deadline
                diff = self.requested_from - requested
                self.requested_from = requested
                self.requested_to = self.requested_to - diff
                self.deadline = self.deadline - diff


    def change_deadline(self, deadline):
        ''' if booking is not complete, then change requested date based on deadline
        '''
        if self.deadline != deadline:
            self.deadline = deadline

            # once booked, can't change time
            if self.status < BOOKING_BOOKED:

                # only change requested time if deadline changed to before current
                # requested time
                if self.deadline < self.requested_to:
                    self.requested_from = self.deadline - timedelta(seconds= self.duration*60)
                    self.requested_to = self.deadline




    def change_requested_from(self, requested):

        # once booked, can't change time
        if self.status < BOOKING_BOOKED:

            self.requested_from = requested




    def change_requested_to(self, requested):

        # once booked, can't change time
        if self.status < BOOKING_BOOKED:

            self.requested_to = requested


    def change_duration(self, duration):

        # once booked, can't change time
        if self.status < BOOKING_BOOKED:
            self.duration = duration

            # only change times if changing duration has caused them to fall outside
            # current times
            new_from = self.deadline - timedelta(seconds= self.duration*60)
            if new_from < self.requested_from:
                self.requested_from = new_from



    @classmethod
    def create_booking(cls, who, when=None, where=None, what=None, deadline=None, client_ref=None, how=None,
                       comments=None, client=None, commit=False):
        """create a new booking record.

        By default, creates a new record with a status of 0 (BOOKING_CREATING) which will be
        immediately edited.  The reason for creating a 0 record is so that the reference can
        be generated and used in the front end.  0 should be deleted by the front end if they
        are not used or will be cleaned up using Booking.delete_temps called by celery/cron.

        This 0 booking doesn't become a "real" booking until it is saved and the status goes to 1
        (BOOKING_REQUESTED) (see self.create)

        To create a "real" booking, use commit = True, and it is then saved with status of 1

        All parameters are optional except who - the user who is creating the booking.

        :param who: user object
        :param when: - a datetime that specifies the start time of the booking OR a two element list
            specifying start and end of booking as datetime
        :param where:
        :param what:
        :param deadline:
        :param client_ref:
        :param how:
        :param comments: if text is passed, is added as a comment object linked to this booking
        :param client: defaults to the client of the user passed to who, otherwise a client object
        :param commit: default False, False to create booking with status BOOKING_CREATING and
            True to create a booking with status BOOKING_REQUESTED
        :return:
        """

        # if activity not specified, get default
        if not how:
            activity = Activity.default_activity()
        else:
            # convert name to object if passed as a string
            if how == unicode(how):
                try:
                    activity = Activity.objects.get(name=how)
                except Activity.DoesNotExist:
                    raise InvalidActivity

                    # else assume activity is an object, it will fail further down if not


        # get start and end times for booking

        # if only date passed, then use default start time
        if deadline and not hasattr(deadline, 'hour'):
            deadline = default_deadline(deadline)

        #not times specified
        if not deadline and not when:
            deadline = default_deadline()
            from_time = default_start(deadline)
            to_time = default_end(from_time)

        elif deadline and not when:
            from_time = default_start(deadline)
            to_time = default_end(from_time)

        # make deadline same as to_time if not specified
        elif when:

            if is_list(when):
                if len(when) == 2:
                    from_time = make_time(when[0],"start")
                    to_time = make_time(when[1], "end")
                else:
                    pass
                    # TODO: raise error
            else:

                from_time = make_time(when,"start")
                to_time = default_end(from_time)

            if not deadline:
                deadline = to_time



        # validation

        # make sure deadline is a datetime
        if not hasattr(deadline, 'hour'):
            deadline = datetime.combine(deadline, time(23, 59))

        # ensure deadline is timezone aware
        deadline = add_tz(deadline)

        if deadline < from_time:
            raise DeadlineBeforeBookingException


        # can't bookin in the past
        # TODO: Allow bookings in the past but only as completed bookings - ie. for payments/records purposes


        if to_time.date() < NOW.date() and not who.is_admin:
            raise PastDateException



        if not client:
            try:
                client = who.client
            except:
                pass





        booking = Booking.objects.create(booker=who,
                                         activity = activity,
                                         client = client,
                                         requested_from = from_time,
                                         requested_to = to_time,
                                         requested_at = NOW,
                                         )

        if where:
            booking.studio = where
        else:
            if booking.client:
                # make studio and instrument default if they are the only ones
                studios = booking.client.studios
                if len(studios) > 0:
                    booking.studio = studios[0]




        if what:
            #TODO: prevent instruments not belonging to this org
            booking.instrument = what
        else:
            if booking.client:
                # make studio and instrument default if they are the only ones
                instruments = booking.client.instruments
                if len(instruments) > 0:
                    booking.instrument = instruments[0]

        if deadline:
            booking.deadline = deadline
        if client_ref:
            booking.client_ref = client_ref

        if commit:
            status = BOOKING_REQUESTED


        booking.save()


        return booking


    def set_booked(self, tuner, start_time=None, duration= settings.DEFAULT_SLOT_TIME, user=None):
        """
        :param tuner: required - tuner object
        :param start_time: optional - the datetime the tuning is to start otherwise defaults
            to requested_from time
        :param duration:
        :return:
        """
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


        self.log(comment="Tuner %s assigned" % (self.tuner,), user=user, type="BOOK")

        # send notification

        send_notification([self.tuner], "booking_confirmed", {"booking": self,
                                                               "description": self.text_description_for_user(self.tuner)
            })
        send_notification([self.booker], "booking_confirmed", {"booking": self,
                                                               "description": self.text_description_for_user(self.booker)
            })
        send_notification(add_admins([]), "booking_confirmed", {"booking": self,
                                                               "description": self.description
            })

        PhoneNumber.release(self)

    @property
    def sms_number(self):
        """

        :return: sms number if one is allocated to this booking otherwise None
        """
        try:
            num = PhoneNumber.objects.get(booking = self)
            return num.number
        except:
            return None

    def get_sms_number(self):
        """
        :return: sms number for this booking, creating one if necessary
        """

        num =  PhoneNumber.get_number(self)
        return "%s" % num.number

    def release_sms_number(self):
        """ frees up the sms number for next booking
        :return: nothing
        """
        qs = PhoneNumber.objects.filter(booking=self)
        if qs.count() > 0:
            #should be only 1
            for item in qs:
                item.booking = None
                item.save()

        return


    def set_complete(self, user=None):

        self.status = BOOKING_COMPLETE
        self.completed_at = NOW
        self.save()

        self.generate_invoice()

        self.log(comment="%s complete" % (self.activity,), user=user, type="COMPLETE")


    def generate_invoice(self):
        '''
        email invoice
        :return:
        '''
        # currently code in web.view
        pass

    def set_uncomplete(self, user=None):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.completed_at).seconds < 90:

            self.status = BOOKING_BOOKED
            self.completed_at = None
            self.save()

            self.log(comment="%s unmarked as complete" % (self.activity,), user=user, type="UNCOMPLETE")

    def set_provider_paid(self, user=None):

        self.paid_provider_at = NOW

        if self.paid_client_at:
            self.set_archived()
        else:
            self.status = BOOKING_PROVIDER_PAID

        self.save()

        self.log(comment="provider paid", user=user, type="PROVIDER_PAID")



    def set_provider_unpaid(self, user=None):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.paid_provider_at).seconds < 90:

            # reset status
            if self.paid_client_at:
                self.status = BOOKING_CLIENT_PAID
            else:
                self.status = BOOKING_COMPLETE


            self.paid_provider_at = None
            self.save()
            self.log(comment="provider unmarked as paid", user=user, type="UNPROVIDER_PAID")

    def set_client_paid(self, user=None):

        self.paid_client_at = NOW

        if self.paid_provider_at:
            self.set_archived()
        else:
            self.status = BOOKING_CLIENT_PAID

        self.save()
        self.log(comment="client paid", user=user, type="CLIENT_PAID")




    def client_unpaid(self, user=None):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.paid_client_at).seconds < 90:

            # reset status
            if self.paid_provider_at:
                self.status = BOOKING_PROVIDER_PAID
            else:
                self.status = BOOKING_COMPLETE

            self.paid_client_at = None
            self.save()
            self.log(comment="client unmakred as paid", user=user, type="UNCLIENT_PAID")



    def set_archived(self, user=None):

        self.status = BOOKING_ARCHIVED
        self.archived_at = NOW
        self.save()
        self.log(comment="archived",  user=user,type="ARCHIVED")


    @classmethod
    def delete_temps(cls):
        ''' delete bookings with status of 0 more than 24 hours old
        RUN VIA CRON web.cron.CheckBookingStatus
        '''

        cls.objects.filter(status=BOOKING_CREATING, booked_time__lt=YESTERDAY).delete()



    @classmethod
    def check_to_complete(cls):
        ''' once a booking has past the status become TOCOMPLETE
        RUN VIA CRON web.cron.CheckBookingStatus
        '''

        n = 0
        for item in cls.objects.filter(status=BOOKING_BOOKED, booked_time__lt=NOW):
            item.set_complete()
            item.save()
            n += 1

        return n




class TunerCallPassThroughManager(PassThroughManager):

    def get_queryset(self):
        return super(TunerCallPassThroughManager, self).get_queryset()


class TunerCallQuerySet(QuerySet):

    def unsent(self):
        return self.filter(status=CALL_INITIALISING)

    def overdue(self):
        return self.filter(booking__deadline__gt = NOW).select_related()

class PhoneNumber(models.Model):


    number = models.CharField(_("twilio number"), max_length=15, unique=True)
    provisioned_at = models.DateTimeField(auto_now_add=True, editable=False)
    booking = models.ForeignKey(Booking, blank=True, null=True)

    def __unicode__(self):
        return self.number

    @classmethod
    def sync(cls):
        """ make sure list is the same as the twilio numbers.
        Load any that are missing.
        Delete any that don't have bookings that are not found.
        If there are ones with bookings that are not found, then reassign the booking to a valid one

        :return:
        """

        # first check all twilio numbers are in table
        numbers = twilio_client.phone_numbers.list()
        checked = []

        for num in numbers:

            try:
                item = cls.objects.get(number = num.phone_number)
            except cls.DoesNotExist:
                item = cls.objects.create(number = num.phone_number)

            checked.append(item)


        # now see if there are any in the table not in twilio
        for item in cls.objects.all():

            if item not in checked:
                booking = None

                #if booking associated with this and booking still active, move to another number
                if item.booking and item.booking.status < BOOKING_COMPLETE:
                    booking = item.booking

                item.delete()

                if booking:
                    cls.get_number(booking)


    @classmethod
    def get_number(cls, booking):
        """
        :return: number to use to send sms
        """

        # first see if already set
        try:
            use = cls.objects.get(booking=booking)
            return use

        except cls.DoesNotExist:
            # then see if a number if free
            available = cls.objects.filter(booking=None).order_by("?")
            if available.count() > 0:
                use = available[0]

            else:
                #otherwise purchase a new number
                use = cls.new_number()


            # save booking against this number
            use.booking = booking
            use.save()

            return use


    @classmethod
    def new_number(cls):

        if settings.TWILIO_DRY_MODE:
            rand = random.randint(10000000, 99999999)
            new = cls.objects.create(number=rand)

        else:

            numbers = twilio_client.phone_numbers.search(country="GB",
            type="local")


            if numbers:
                result = numbers[0].purchase()
                new = cls.objects.create(number = result.phone_number)


        return new

    @classmethod
    def release(cls, booking):

        try:
            item = cls.objects.get(booking=booking)
            item.booking = None
            item.save()
        except cls.DoesNotExist:
            pass



class TunerCall(models.Model):

    #TODO: delete tunercall relating to booking when booking is deleted (as opposed to cancelled)
    CALL_STATUS = ((CALL_INITIALISING, 'Initialising'),
                   (CALL_WAITING, 'Pending'),
                   (CALL_REJECTED, 'Rejected'),
                   (CALL_ACCEPTED, "Accepted"),
                   (CALL_EXPIRED, 'Expired'),
                   (CALL_FAILED, 'Call Failed'),
    )

    booking = models.ForeignKey(Booking)
    tuner = models.ForeignKey(Tuner, blank=True, null=True)
    initiated = models.DateTimeField(auto_now_add=True, editable=False)
    called = models.DateTimeField(blank=True, null=True)
    expire_in =  models.PositiveSmallIntegerField(_('Expire in mins after call'), default=5)
    status = models.CharField(max_length=1, choices=CALL_STATUS, default=CALL_INITIALISING)
    twilio_status = models.CharField(max_length=20, blank=True, null=True)
    twilio_status_updated = models.DateTimeField(blank=True, null=True)
    answered = models.DateTimeField(blank=True, null=True)
    sms_sid = models.CharField(max_length=24, blank=True, null=True)
    objects = TunerCallPassThroughManager.for_queryset_class(TunerCallQuerySet)()


    def __unicode__(self):
        return "%s re %s" % (self.tuner, self.booking)


    class Meta:
        ordering = ['-id',]
        unique_together = ['booking','tuner']


    @transaction.atomic()
    def save(self, *args, **kwargs):

        super(TunerCall, self).save(*args, **kwargs)

        # id of the TunerCall record is passed to notification so that the SID from twillio can be added to the record.
        if  self.tuner and not self.called and (self.tuner.is_contactable):
            send_notification([self.tuner,], "tuner_request", {"tunercall_id": self.id,
                                                               "booking": self.booking,
                                                               "description": self.booking.description_for_user(self.tuner)
            })
            self.called = NOW

            super(TunerCall, self).save(*args, **kwargs)


    @classmethod
    def request_all(self, booking):

        for tuner in Tuner.objects.filter(active=True):
            call = TunerCall.objects.create(booking = booking, tuner=tuner)


    @classmethod
    def request(self, booking):


        while True:
            call = TunerCall(booking = booking)
            tuner = call.get_next_tuner()
            # loop until run out of tuners to call
            if not tuner:
                break
            call.tuner = tuner
            call.save()




        # code for calling one at a time
        # if tuner:
        #     call.tuner = tuner
        # else:
        #     call.msg_no_tuners()
        #     print "Failed to send request for booking %s" % self.booking
        #     raise RequestTunerFailed


        # call.save()
        # return call

    def get_next_tuner(self):

        already_called = self.already_called()
        remaining = Tuner.objects.exclude(id__in = already_called).order_by('-score',)

        # nobody left
        if remaining.count() < 1:
            return None

        for tuner in remaining:
            if tuner.is_available(self.booking):
                return tuner
                break

        # nobody left who is available
        return None

    def already_called(self):
        '''
        :return:list of tuner ids that have already been called for this booking
        '''
        uncalled = TunerCall.objects.filter(booking=self.booking).values_list('tuner',).exclude(tuner__isnull=True)
        # uncalled = a list of lists, so flatten before returning
        return [item for sublist in uncalled for item in sublist]

    @transaction.atomic()
    def tuner_accepted(self):

        self.status = CALL_ACCEPTED
        self.answered = NOW
        self.save()
        self.booking.set_booked(tuner=self.tuner)

        # expire rest of calls
        for item in TunerCall.objects.filter(booking = self.booking, status=CALL_WAITING):
            item.status = CALL_EXPIRED
            item.save()
        self.msg_call_expired()




    def tuner_rejected(self):

        self.status = CALL_REJECTED
        self.answered = NOW
        self.save()




    def msg_no_tuners(self):

        msg = []

        subject = "NOT TUNERS AVAILABLE FOR %s?" % (self.booking.short_description)
        body = """See full details: %s

            """ % (self.booking.get_absolute_url())

        # extract list of emails
        to = map((lambda  d:  d[1]), settings.ADMINS)

        msg.append([subject, body, to])
        self.booking.send_msgs(msg)

    def msg_call_expired(self):

        msg = []

        subject = "Tuner no longer required for " % (self.booking.short_description)
        body = """See full details: %s

            """ % (self.booking.get_absolute_url())

        # extract list of emails
        to = TunerCall.objects.filter(booking=self.booking, status=CALL_EXPIRED).values_list('tuner__email')

        msg.append([subject, body, to])
        self.booking.send_msgs(msg)

    def expire(self):
        self.status = CALL_EXPIRED
        self.save()



class LogPassThroughManager(PassThroughManager):

    def get_queryset(self):
        return super(LogPassThroughManager, self).get_queryset()


class LogQuerySet(QuerySet):


    def mine(self, user):

        # booker can see all bookings for the client
        if user.is_booker:
            return self.filter(booking__client=user.client)

        elif user.is_tuner:
            # all this tuners bookings and bookings looking for tuners
            return self.filter(booking__tuner=user).exclude(status = 7)

        elif user.is_admin:
            return self

        else:
            raise InvalidQueryset(message = "user %s must be booker, tuner or admin" % user)


class Log(models.Model):
    """
    Record interesting activity
    """

    booking = models.ForeignKey(Booking)
    status = models.CharField(max_length=1, default=" ")
    comment = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(CustomUser, blank=True, null=True)
    log_type = models.CharField(max_length=20, default='user')

    objects = LogPassThroughManager.for_queryset_class(LogQuerySet)()

    def __unicode__(self):
        return self.comment

    class Meta:
        ordering = ['-created',]

    def save(self, *args, **kwargs):

        # save status of booking at the time the comment was made
        if self.booking:
            self.status = self.booking.status

        super(Log, self).save(*args, **kwargs)




class CustomAuth(ModelBackend):

    def get_user(self, user_id):

        try:
            return Booker._default_manager.get(pk=user_id)
        except Booker.DoesNotExist:
            try:
                return Tuner._default_manager.get(pk=user_id)
            except Tuner.DoesNotExist:
                try:
                    return CustomUser._default_manager.get(pk=user_id)
                except CustomUser.DoesNotExist:
                    return None
        return None

