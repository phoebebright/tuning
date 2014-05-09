import uuid
from decimal import *

from datetime import datetime, date, timedelta, time


from django.conf import settings
from django.contrib.auth.models import  AbstractUser, UserManager
from django.contrib.contenttypes.models import ContentType

from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import  MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.http import  Http404
from django.template import Context, Template
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.backends import ModelBackend


from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from model_utils.managers import QueryManager, PassThroughManager


from libs.utils import make_time, is_list, add_tz
from web.exceptions import *

from django_google_maps import fields as map_fields
from django.forms.models import model_to_dict
from django_gravatar.helpers import get_gravatar_url




"""
notifications:
https://github.com/tomchristie/django-ajax-messages - auto refreshing
https://github.com/AliLozano/django-messages-extends
https://github.com/scdoshi/django-notifier - build different backends for sms etc.
http://www.twilio.com/sms/pricing/gb - sending sms

"""

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
BOOKING_CANCELLED = "8"    # tuning has been done but not yet paid
BOOKING_ARCHIVED = "9"    # paid and finished

# default booking request times

def default_start():
    return datetime.combine(TOMORROW, time(12, 00))

def default_end():
   return datetime.combine(TOMORROW, time(12, 30))

def default_start_time(deadline):

    if deadline:
        return make_time(deadline - timedelta(minutes = settings.DEFAULT_SLOT_TIME))
    else:
        return None

def system_user():

    try:
        return CustomUser.objects.get(username='system')
    except CustomUser.DoesNotExist:
        raise NoSystemUser

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
    return Decimal(price * Decimal('0.66'))






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
    name = models.CharField(_('eg Tuning'), max_length=12, unique=True)
    name_plural = models.CharField(_('eg. Tunings'), max_length=15)
    name_verb = models.CharField(_('eg. Tune'), max_length=20)
    name_verb_past =   models.CharField(_('eg. Tuned'), max_length=20)
    duration = models.PositiveIntegerField(_('Default time slot in minutes '), max_length=5, default=60)
    order = models.PositiveSmallIntegerField(_('Order to display in lists'), default=0)
    price = models.DecimalField(_('Default price (ex vat)'), max_digits=10, decimal_places=2, default=50)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']

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



    def save(self, *args, **kwargs):

        if 'email' in self.changed_fields or not self.gravatar:
            self.gravatar = get_gravatar_url(self.email, size=80)

        super(CustomUser, self).save(*args, **kwargs)


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

    @property
    def is_admin(self):
        return self.is_staff

    @property
    def can_book(self):
        return self.is_staff

    @property
    def can_see_price(self):
        return self.is_staff or self.is_booker

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
            return ""

        # booker sees all for this client
        if self.is_booker:
            return "{client_id:%s}" % self.client_id

        # booker sees all for this client
        if self.is_tuner:
            return "{user_id:%s}" % self.id


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


        #TODO: may want to limit users who can create bookings

        booking = Booking.create_booking(self, when, where, what, deadline, client_ref, how, comments )


        return booking


class Tuner(CustomUser):

    provider = models.ForeignKey(Provider, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    geolocation = map_fields.GeoLocationField(max_length=100, blank=True, null=True)
    activities = models.ManyToManyField(Activity, blank=True, null=True)
    #TODO: add vat registered

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

class BookingsPassThroughManager(PassThroughManager):

    def get_queryset(self):
        return super(BookingsPassThroughManager, self).get_queryset().filter(client__isnull=False)


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

        if user.is_booker:
            return self.filter(booker=user)

        elif user.is_tuner:
            return self.filter(tuner=user)

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

    ref = models.CharField(max_length=10, unique=True)
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
    client_ref = models.CharField(_('session reference'), max_length=20, blank=True, null=True)

    price = models.DecimalField(_('Price for job ex vat'), max_digits=10, decimal_places=2, default=0)
    default_price = models.DecimalField(_('System calculated price for job ex vat'), max_digits=10, decimal_places=2, default=0)
    tuner_payment = models.DecimalField(_('Amount due to Tuner'), max_digits=10, decimal_places=2, default=0)
    vat = models.DecimalField(_('VAT Amount'), max_digits=10, decimal_places=2, default=vat_rate())


    objects = BookingsPassThroughManager.for_queryset_class(BookingsQuerySet)()


    def __unicode__(self):
        return "%s %s on %s %s " % (self.ref, self.studio, self.when.strftime('%b'), self.when.strftime('%d'))

    def get_absolute_url(self):
        return reverse('booking-detail', kwargs={'pk': self.pk})

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
                self.ref = Booking.create_ref(self.studio, self.deadline)

            self.activity = Activity.default_activity()
            self.requested_at = NOW
            self.recalc_prices(user)

        if 'price' in self.changed_fields:
            # recalc vat
            self.vat = self.default_price * vat_rate()
            self.tuner_payment = tuner_pay(self.price)
        else:
            if 'requested_at' in self.changed_fields:
                self.recalc_prices(user)



        # change status to archived  when fully paid
        # TODO:test
        if self.status == BOOKING_COMPLETE and self.paid_provider_at and self.paid_client_at:
            self.status=BOOKING_ARCHIVED
            self.archived_at = NOW

        super(Booking, self).save(*args, **kwargs)

    def recalc_prices(self, user=None):
        #NOTE: does not save
        old_price = self.price

        self.default_price = self.get_default_price() * Decimal(str(self.duration)) / Decimal('60.00')
        self.vat = self.default_price * vat_rate()
        self.price = self.default_price
        self.tuner_payment = tuner_pay(self.price)

        if user and old_price != self.price:
            add_message(user, "Price has changed!")

        return {'default_price': self.default_price,
                'vat': self.vat,
                'price': self.price,
                'tuner_payment': self.tuner_payment}

    @classmethod
    def create_temp_ref(cls):

        code = str(uuid.uuid4())[:6]
        while True:
            try:
                used = Booking.objects.get(ref = code)
                code = str(uuid.uuid4())[:6]
            except Booking.DoesNotExist:
                # not found so is unique
                return code


    @classmethod
    def create_ref(cls, studio=None, deadline=None):

        if not studio or not deadline:
            return Booking.create_temp_ref()

        code = "%s-%s%sa" % (studio.short_code, deadline.strftime('%b'), deadline.strftime('%d'))
        while True:
            try:
                used = Booking.objects.get(ref = code)
                code = code[:-1] + chr(ord(used.ref[-1]) + 1)
            except Booking.DoesNotExist:
                # not found so is unique
                return code

    @property
    def has_temp_ref(self):
        return len(self.ref) == 6

    @property
    def short_heading(self):
        return self.ref

    @property
    def long_heading(self):
        return "%s (%s)" % (self.client, self.ref)


    def description_for_user(self, user):
        '''
        :return:includes money
        '''

        base = self.description

        if user.is_admin:
            return "%s charging %s%s paying %s%s" % (base, "&pound", self.price, "&pound", self.tuner_payment)

        if user.is_booker:
            return "%s%s ex VAT" % (base, "&pound", self.price)

        if user.is_tuner:
            return "%s  paying %s%s" % (base,  "&pound", self.tuner_payment)

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
                txt = "%s to %s " % (self.tuner, self.activity.name_verb)
            else:
                txt = "%s %s " % (self.tuner, self.activity.name_verb_past)
        else:
            txt = ""

        if self.instrument:
            txt += "%s " % self.instrument


        if self.studio:
            txt += "at %s " % self.studio


        if self.deadline:
            txt  += "for session starting at %s " % (formats.date_format(self.deadline, "DATETIME_FORMAT"), )

        if self.client_ref:
            txt += "with ref %s " % self.client_ref

        return txt

    @property
    def comments(self):
        return Log.objects.filter(booking=self)

    @property
    def start_time(self):

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


    def create(self, user=None):

        #TODO: some validation here
        if  int(self.status) == 0:
            self.status = BOOKING_REQUESTED
            self.booked_at = NOW
            self.save()

            # notifications
            msg = "New %s added for %s for %s with ref %s" % (self.activity.name, self.client, self.deadline.strftime("%a %d %B at %H:%m"), self.ref)

            self.log(comment=msg, user=user, type='CREATE')

    def cancel(self, user=None):

        # if not created then just delete
        if self.status == 0:
            #TODO: delete comments
            self.delete()

        else:

            #TODO: test
            #TODO: prevent cancellation when status is complete
            #TODO: can only be cancelled by admin or person who created
            self.cancelled_at = NOW
            self.status = BOOKING_CANCELLED
            self.save()

            # notifications
            msg = "Booking CANCELLED to %s for %s for %s with ref %s" % (self.activity.name, self.client, self.deadline.strftime("%a %d %B at %H:%m"), self.ref)
            self.log(comment=msg, user=user, type='CANCEL')


    def change_deadline(self, deadline):
        ''' if booking is not complete, then change requested date based on deadline
        '''
        if self.deadline != deadline:
            self.deadline = deadline

            if self.status < '2':
                self.requested_from = self.deadline - timedelta(seconds= self.duration*60)
                self.requested_to = self.deadline

            self.save()





    @classmethod
    def create_booking(cls, who, when=None, where=None, what=None, deadline=None, client_ref=None, how=None, comments=None, client=None, ):

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
        if is_list(when):
            if len(when) == 2:
                from_time = make_time(when[0])
                to_time = make_time(when[1])
            else:
                pass
                # TODO: raise error
        else:
            if when:
                from_time = make_time(when, "start")
                to_time = make_time(when, "end")
                # can't bookin in the past
                # TODO: Allow bookings in the past but only as completed bookings - ie. for payments/records purposes
                # commented out for the moment to make testing easier
                if to_time < NOW:
                    raise PastDateException

            else:
                from_time = default_start_time(deadline)
                to_time = make_time(deadline)





        # fix end time if possible

        if deadline:


            # make sure deadline is a datetime
            if not hasattr(deadline, 'hour'):
                deadline = datetime.combine(deadline, time(23, 59))

            # ensure deadline is timezone aware
            deadline = add_tz(deadline)


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

        self.log(comment="Tuner %s assigned" % (self.tuner,), type="BOOK")


    def set_complete(self):

        self.status = BOOKING_COMPLETE
        self.completed_at = NOW
        self.save()

        self.log(comment="%s complete" % (self.activity,), type="COMPLETE")

    def set_uncomplete(self):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.completed_at).seconds < 90:

            self.status = BOOKING_BOOKED
            self.completed_at = None
            self.save()

            self.log(comment="%s unmarked as complete" % (self.activity,), type="UNCOMPLETE")

    def set_provider_paid(self):

        self.paid_provider_at = NOW

        if self.paid_client_at:
            self.status = BOOKING_ARCHIVED

        self.save()

        self.log(comment="provider paid", type="PROVIDER_PAID")


    def set_provider_unpaid(self):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.paid_provider_at).seconds < 90:

            self.status = BOOKING_COMPLETE
            self.paid_provider_at = None
            self.save()
            self.log(comment="provider unmarked as paid", type="UNPROVIDER_PAID")

    def set_client_paid(self):

        self.paid_client_at = NOW

        if self.paid_provider_at:
            self.status = BOOKING_ARCHIVED

        self.save()
        self.log(comment="client paid", type="CLIENT_PAID")


    def client_unpaid(self):
        ''' set status back, but only if called  within a minute(ish)
        '''

        if (NOW - self.paid_client_at).seconds < 90:

            self.status = BOOKING_COMPLETE
            self.paid_client_at = None
            self.save()
            self.log(comment="client unmakred as paid", type="UNCLIENT_PAID")

    def send_request(self):
        # schedule email http://www.cucumbertown.com/craft/scheduling-morning-emails-with-django-and-celery/
        subject = "Can you tune for %s between %s and %s" % (self.client.name, self.start_time, self.end_time)
        message = "To Tune %s in %s for session %s starting at %s" % (self.instrument, self.studio, self.client_id, self.deadline)
        to_email = "phoebebright310@gmail.com"
        from_email = "tuning@trialflight.com"


        send_mail(subject, message, from_email, [to_email,], fail_silently=True)


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

        for item in cls.objects.filter(status=BOOKING_BOOKED, booked_time__lt=NOW):
            item.status = BOOKING_TOCOMPLETE
            item.save()


class Log(models.Model):
    """
    Record interesting activity
    """

    booking = models.ForeignKey(Booking)
    comment = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(CustomUser, blank=True, null=True)
    log_type = models.CharField(max_length=20, default='U')

    def __unicode__(self):
        return self.comment

    class Meta:
        ordering = ['-created',]



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
