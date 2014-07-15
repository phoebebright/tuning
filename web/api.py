import urlparse
from django.utils.timezone import is_aware
import arrow
import json

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.http import HttpRequest

from tastypie import fields
from tastypie.authentication import SessionAuthentication, Authentication, BasicAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization, ReadOnlyAuthorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound, BadRequest
from tastypie.paginator import Paginator
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.serializers import Serializer


from web.models import *


from django.contrib.auth import get_user_model

User = get_user_model()


'''
NOTE: TIMEZONE handling = None!
'''
class urlencodeSerializer(Serializer):
    #http://stackoverflow.com/questions/14074149/tastypie-with-application-x-www-form-urlencoded
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'urlencode']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'urlencode': 'application/x-www-form-urlencoded',
        }
    def from_urlencode(self, data,options=None):
        """ handles basic formencoded url posts """
        qs = dict((k, v if len(v)>1 else v[0] )
                  for k, v in urlparse.parse_qs(data).iteritems())
        return qs

    def to_urlencode(self,content):
        pass

from tastypie.serializers import Serializer


class CustomSerializer(Serializer):
    """
    Output TZ aware string
    """
    def format_datetime(self, data):
        dt = timezone.localtime(data)
        return super(CustomSerializer, self).format_datetime(dt)


class SimpleObject(object):
    def __init__(self, id=None, name=None, value=None):
        self.id = id
        self.name = name
        self.value = value


class RequestBookingResource(ModelResource):
    class Meta:
        allowed_methods = ['post']
        object_class = Booking
        resource_name = 'request'
        authentication = Authentication()
        authorization = Authorization()
        include_resource_uri = False


    def obj_create(self, bundle, request=None, **kwargs):
        try:
            bundle.obj = Booking.request(bundle.data['username'],bundle.data['from'],bundle.data['to'])
        except IntegrityError:
            raise BadRequest('That username already exists')
        return bundle



class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        fields = ['first_name', 'last_name', 'email', 'mobile']
        resource_name = 'user'
        limit = 0
        include_resource_uri = False
        list_allowed_methods = ['get', ]
        detail_allowed_methods = ['get',]

    def dehydrate(self, bundle):

        bundle.data['full_name'] = bundle.obj.get_full_name()
        return bundle


class CustomUserResource(ModelResource):
    class Meta:
        queryset = CustomUser.objects.all()
        fields = []
        resource_name = 'customuser'
        limit = 0
        include_resource_uri = False
        list_allowed_methods = ['get', ]
        detail_allowed_methods = ['get',]

    def dehydrate(self, bundle):


        bundle.data['full_name'] = bundle.obj.get_full_name()

        return bundle
class ClientResource(ModelResource):
    class Meta:
        queryset = Client.objects.active()
        include_resource_uri = False
        resource_name = 'clients'
        limit = 0
        allowed_methods = ['get']


class ProviderResource(ModelResource):
    class Meta:
        queryset = Provider.objects.active()
        include_resource_uri = False
        resource_name = 'providers'
        limit = 0
        allowed_methods = ['get']


class TunerResource(ModelResource):
    class Meta:
        queryset = Tuner.objects.all()
        include_resource_uri = False
        resource_name = 'tuners'
        limit = 0
        allowed_methods = ['get']

    def dehydrate(self, bundle):
        bundle.data['full_name'] = bundle.obj.get_full_name()

        return bundle

class BookerResource(ModelResource):
    # client = fields.ToOneField(ClientResource, "client", full=False)  not used, if used needs to be null=True in case admin user is booking?

    class Meta:
        queryset = Booker.objects.filter(is_active=True).select_related()
        fields = ['id',]
        include_resource_uri = False
        resource_name = 'bookers'
        limit = 0
        allowed_methods = ['get',]
        filtering = {
            'client_id': ['exact', ]
        }



    def dehydrate(self, bundle):
        bundle.data['full_name'] = bundle.obj.get_full_name()

        return bundle



class ClientMinResource(ModelResource):
    class Meta:
        queryset = Client.objects.all()
        include_resource_uri = False
        fields = ['id', 'name']
        limit = 0
        resource_name = 'minclient'
        allowed_methods = ['get']

class ActivityResource(ModelResource):
    class Meta:
        queryset = Activity.objects.all()
        include_resource_uri = False
        limit = 0
        resource_name = 'activities'
        allowed_methods = ['get']

class StudioResource(ModelResource):
    client = fields.ToOneField(ClientResource, "client", full=False)

    class Meta:
        queryset = Studio.objects.all()
        include_resource_uri = False
        resource_name = 'studios'
        limit = 0
        allowed_methods = ['get',]
        filtering = {
            'client_id': ['exact', ]
        }

    def get_object_list(self, request):
        base = super(StudioResource, self).get_object_list(request)
        if request._get.has_key('client_id'):
            return base.filter(client_id = request._get['client_id'])
        else:
            return base

class InstrumentResource(ModelResource):
    client = fields.ToOneField(ClientResource, "client", full=False)

    class Meta:
        queryset = Instrument.objects.all()
        include_resource_uri = False
        resource_name = 'instruments'
        limit = 0
        allowed_methods = ['get']
        filtering = {
            'client_id': ['exact', ]
        }

    def get_object_list(self, request):
        base = super(InstrumentResource, self).get_object_list(request)
        if request._get.has_key('client_id'):
            return base.filter(client_id = request._get['client_id'])
        else:
            return base


class BookingsResource(ModelResource):
    #TODO: Only return own bookings
    ''' can pass status = current or status = archived or the numeric value of the status required
    '''


    class Meta:
        queryset = Booking.objects.current()
        include_resource_uri = True
        resource_name = 'bookings'
        allowed_methods = ['get']
        limit = 0
        fields = ['ref','requested_from','requested_to','studio','instrument', 'status', 'deadline','client',
                  'booker_id','tuner_id','activity', 'duration', 'client_ref', 'price', 'default_price', 'tuner_payment', 'vat']
        filtering = {
            'client_id': ('exact',),
            'status': ('exact',),
            'ref': ('exact',),
            # 'dataset': ('exact',),
            }
        #
        # authorization = Authorization()
        # authentication = GMDAuthentication()

    def dehydrate(self, bundle):
        # for fullCalendar
        # see http://arshaw.com/fullcalendar/docs2/event_data/Event_Object/

        # qs = Booking.objects.raw('SELECT * FROM foo_bar')
        # return [row for row in qs]

        bundle.data['title'] = bundle.obj.long_heading

        bundle.data['client_id'] = bundle.obj.client_id

        if bundle.obj.start_time:
            bundle.data['start'] = bundle.obj.start_time
        else:
            bundle.data['start'] = ''

        if bundle.obj.end_time:
           bundle.data['end'] = bundle.obj.end_time
        else:
            bundle.data['end'] = ''

        bundle.data['status_display'] = bundle.obj.get_status_display()

        bundle.data['who'] = bundle.obj.who

        if bundle.obj.when:

            bundle.data['when'] = bundle.obj.when
        else:
            bundle.data['when'] = ''


        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what

        bundle.data['description'] = bundle.obj.description_for_user(bundle.request.user)

        # set true if booking active and this user can change
        bundle.data['editable'] = bundle.obj.is_editable(bundle.request.user)

        #bundle.data['activity'] = bundle.obj.activity.name

        return bundle

    def get_object_list(self, request):
        base = super(BookingsResource, self).get_object_list(request)

        # if empty no more filtering otherwise limit to current users bookings
        if not base:
            return base
        else:
            base = base.mine(request.user)


        try:
            if request._get.has_key('dataset'):
                dataset = request._get.get('dataset')
                if dataset.lower() == "current":
                    base =  base.current()
                elif dataset.lower() == "archived":
                    base = base.archived()


            if request._get.has_key('start'):
                start = datetime.strptime(request._get['start'], "%Y-%m-%d")
                base = base.filter(deadline_gte = start)

            if request._get.has_key('end'):
                end = datetime.strptime(request._get['end'], "%Y-%m-%d")
                base = base.filter(deadline_lte = end)

            return base
        except:
            # above will fail if called from view as no _get
            return base


class BookingsFullResource(BookingsResource):

    client = fields.ToOneField(ClientResource, "client", full=True)
    booker = fields.ToOneField(BookerResource, "booker", full=True)
    tuner = fields.ToOneField(TunerResource, "tuner", full=True, blank=True, null=True)
    activity = fields.ToOneField(ActivityResource, "activity", full=True, blank=True, null=True)
    instrument = fields.ToOneField(InstrumentResource, "instrument", full=True, blank=True, null=True)
    studio = fields.ToOneField(StudioResource, "studio", full=True, blank=True, null=True)

    class Meta(BookingsResource.Meta):
        queryset = Booking.objects.all()
        resource_name = 'bookings_fat'

    def get_object_list(self, request):
        base = super(BookingsFullResource, self).get_object_list(request)

        return base

    def dehydrate(self, bundle):

        # price goes up as time passes, so recalc prices if booking still not made

        # shouldn't be updating I don't think.
        # if bundle.obj.status <= BOOKING_REQUESTED:
        #     upd = bundle.obj.recalc_prices()
        #     bundle.obj.save(user=bundle.request.user)
        #
        #     bundle.data['default_price'] = upd['default_price']
        #     bundle.data['vat'] = upd['vat']
        #     bundle.data['price'] = upd['price']
        #     bundle.data['tuner_payment'] = upd['tuner_payment']

        from web.views import render_booking_template

        bundle = super(BookingsFullResource, self).dehydrate(bundle)

        # return a rendered editable template for this booking
        #TODO: don't need to populate?  Is done in js populate_form I think
        bundle.data['template'] = render_booking_template(bundle.request, bundle.obj, user=bundle.request.user)
        bundle.data['testing'] = bundle.obj.booker.username
        return bundle


class BookingsCalendarResource(BookingsResource):


    class Meta(BookingsResource.Meta):
        queryset = Booking.objects.all()
        resource_name = 'bookings4calendar'

    def get_object_list(self, request):
        base = super(BookingsCalendarResource, self).get_object_list(request)

        return base.values()


class BookingUpdateResource(Resource):

    booking = None
    user = None

    class Meta:
        include_resource_uri = True
        allowed_methods = ['post','put','get','options']
        include_resource_uri = False
        object_class = SimpleObject
        always_return_data = True
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()



    def obj_create(self, bundle, request=None, **kwargs):


        # if no value then nothing to do
        if not bundle.data.has_key('value'):
            return None

        ref = bundle.data['pk']
        value = bundle.data['value']
        me = bundle.request.user

        try:
            self.booking = Booking.objects.get(ref=ref)
            # self.booking will have the updated booking object which may be used in dehydrate

            self.update_booking(self.booking, bundle, value)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)

        return  bundle

    def update_booking(self, booking, bundle):

        pass

    def obj_get_list(self, bundle, **kwargs):
        raise BadRequest('You are probably calling with get and it should be post')

    def get_resource_uri(self, bundle_or_obj):

        if not bundle_or_obj:
            return None

        kwargs = {
            'resource_name': self._meta.resource_name,
        }


        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj.id


        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url('api_dispatch_detail', kwargs = kwargs)

    def dehydrate(self, bundle):

        # return updated booking resource
        resource = BookingsFullResource()

        if not self.booking:
          self.booking = resource.obj_get(bundle, ref=bundle.data['pk'])

        booking_bundle = resource.build_bundle(obj=self.booking, request=bundle.request)


        bundle.data['booking'] = resource.full_dehydrate(booking_bundle)

        return bundle

class InitBookingResource(BookingUpdateResource):
    '''
    without always_return_data = True the jquery ajax fails with 201 and no response data
    with always_return_data = True it retuns a copy of the post data but what I want is the ID.
    '''

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'init_booking'
        always_return_data = True


    def obj_create(self, bundle, request=None, **kwargs):

        client_id = bundle.data['client_id']

        try:
            client = Client.objects.get(id=client_id)
            if not client.active:
                raise BadRequest('This Client %s is not active' % client)
        except Client.DoesNotExist:
            raise BadRequest('This Client id does not exist: %s' % client_id)


        user = bundle.request.user
        if not user.can_book:
            raise BadRequest('This User %s is not allowed to make bookings' % user)



        if bundle.data.has_key('start'):
            start = arrow.get(bundle.data['start']).datetime

            try:
                self.booking =  Booking.create_booking(user, client=client, when=start)
            except Exception, e:
                bundle = {"code": 777, "status": False, "error": json.loads(e.response.content)}

        elif bundle.data.has_key('deadline'):

            dline = arrow.get(bundle.data['deadline']).datetime

            # was deadline passed as date or datetime
            if len(bundle.data['deadline']) < 11:
                deadline = dline.date()
            else:
                deadline = dline

            self.booking =  Booking.create_booking(user, client=client, deadline=deadline)

        else:
            self.booking =  Booking.create_booking(user, client=client)


        return bundle


class BookingMakeResource(BookingUpdateResource):
    ''' take a booking object that has been created but still has a status of 0
    and change to status = 1 which makes it a real booking
    '''
    class Meta(BookingUpdateResource.Meta):
        resource_name = 'make_booking'


    def update_booking(self, booking, bundle, value):

        booking.make_booking(bundle.request.user)

class BookingDeleteResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'delete_booking'


    def update_booking(self, booking, bundle, value):

        booking.cancel(bundle.request.user)



class BookingActivityResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_activity_booking'


    def update_booking(self, booking, bundle, value):

        try:
            booking.activity = Activity.objects.get(id=value)
            booking.save(user=bundle.request.user)

        except Activity.DoesNotExist:
            raise BadRequest('Invalid Activity id %s' % value)


class BookingInstrumentResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_instrument_booking'


    def update_booking(self, booking, bundle, value):

        try:
            booking.instrument = Instrument.objects.get(id=value)
            booking.save(user=bundle.request.user)

        except Instrument.DoesNotExist:
            raise BadRequest('Invalid Instrument id %s' % value)


class BookingTunerResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_tuner_booking'


    def update_booking(self, booking, bundle, value):

        try:
            booking.tuner = Tuner.objects.get(id=value)
            self.booking = booking.save(user=bundle.request.user)
            #return updated_booking
        except Tuner.DoesNotExist:
            raise BadRequest('Invalid Tuner id %s' % value)


class BookingStudioResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_studio_booking'


    def update_booking(self, booking, bundle, value):

        try:
            booking.studio = Studio.objects.get(id=value)
            booking.save(user=bundle.request.user)
        except Studio.DoesNotExist:
            raise BadRequest('Invalid Studio id %s' % value)

class BookingBookerResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_booker_booking'


    def update_booking(self, booking, bundle, value):

        try:
            booking.booker = Booker.objects.get(id=value)
            booking.save(user=bundle.request.user)
        except Booker.DoesNotExist:
            raise BadRequest('Invalid Booker id %s' % value)

class BookingTimes(BookingUpdateResource):

    class Meta(BookingStudioResource.Meta):
        resource_name = 'set_booking_times'


    def obj_create(self, bundle, request=None, **kwargs):
        # date expected to be utc so no conversion required
        ref = bundle.data['pk']
        #TDOD: error handling

        tm = make_time(datetime.strptime(bundle.data['value'][0:16], "%Y-%m-%dT%H:%M"))
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)
        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)

        booking.change_all_times(bundle.data['time_type'], tm)
        booking.save(user=bundle.request.user)

        return self.full_hydrate(bundle)

class BookingDeadlineResource(BookingUpdateResource):

    class Meta(BookingStudioResource.Meta):
        resource_name = 'set_deadline_booking'


    def obj_create(self, bundle, request=None, **kwargs):
        ''' expecting datetime in utc
        '''
        ref = bundle.data['pk']
        #TDOD: error handling
        deadline = make_time(datetime.strptime(bundle.data['value'][0:16], "%Y-%m-%dT%H:%M"))
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)
        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)

        booking.change_deadline(deadline)
        booking.save(user=bundle.request.user)

        return self.full_hydrate(bundle)


class BookingRequestedStartResource(BookingUpdateResource):

    class Meta(BookingStudioResource.Meta):
        resource_name = 'set_requested_start_booking'


    def obj_create(self, bundle, request=None, **kwargs):
        # date expected to be utc so no conversion required
        ref = bundle.data['pk']
        #TDOD: error handling

        tm = make_time(datetime.strptime(bundle.data['value'][0:16], "%Y-%m-%dT%H:%M"))
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)
        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)

        booking.change_requested_from(tm)
        booking.save(user=bundle.request.user)

        return self.full_hydrate(bundle)

class BookingRequestedEndResource(BookingUpdateResource):

    class Meta(BookingStudioResource.Meta):
        resource_name = 'set_requested_end_booking'


    def obj_create(self, bundle, request=None, **kwargs):
        # date expected to be utc so no conversion required
        ref = bundle.data['pk']
        #TDOD: error handling

        tm = make_time(datetime.strptime(bundle.data['value'][0:16], "%Y-%m-%dT%H:%M"))
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)
        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)

        booking.change_requested_to(tm)
        booking.save(user=bundle.request.user)

        return self.full_hydrate(bundle)

class BookingClientrefResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_clientref_booking'
        include_resource_uri = False

    def update_booking(self, booking, bundle, value):

        booking.client_ref = value
        booking.save(user=bundle.request.user)


class BookingDurationResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_duration_booking'
        include_resource_uri = False

    def update_booking(self, booking, bundle, value):
        #TODO: validation of duration

        booking.change_duration(int(value))
        booking.recalc_prices()
        booking.save(user=bundle.request.user)


class BookingPriceResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'set_price_booking'
        include_resource_uri = False

    def update_booking(self, booking, bundle, value):
        #TODO: validation of duration
        booking.price = value
        booking.vat = Decimal(str(value)) * vat_rate()
        booking.save(user=bundle.request.user)


class BookingCompleteResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'booking_complete'

    def update_booking(self, booking, bundle, value):

        state = bundle.data['state']

        if state == "true":
            booking.set_complete(user=bundle.request.user)
        else:
            booking.set_uncomplete(user=bundle.request.user)



class BookingProviderPaidResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'booking_provider_paid'


    def update_booking(self, booking, bundle, value):


        state = bundle.data['state']

        if state == "true":
            booking.set_provider_paid(user=bundle.request.user)
        else:
            booking.set_provider_unpaid(user=bundle.request.user)


class AcceptBookingResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'accept_booking'

    def update_booking(self, booking, bundle, value):


        tuner_id = bundle.data['value']
        me = bundle.request.user

        tuner = Tuner.objects.get(id=tuner_id)
        booking.set_booked(tuner,user=bundle.request.user)


class BookingClientPaidResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):

        resource_name = 'booking_client_paid'


    def update_booking(self, booking, bundle, value):


        state = bundle.data['state']


        if state == "true":
            booking.set_client_paid(user=bundle.request.user)
        else:
            booking.set_client_unpaid(user=bundle.request.user)


class BookingCancelResource(BookingUpdateResource):

    class Meta(BookingUpdateResource.Meta):
        resource_name = 'booking_cancel'


    def update_booking(self, booking, bundle, value):


        me = bundle.request.user

        booking.cancel(me)





class RecentBookingsResource(ModelResource):
    #TODO: Only return own bookings
    client = fields.ToOneField(ClientResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)
    tuner = fields.ToOneField(UserResource, "tuner", full=True, blank=True, null=True)

    class Meta:
        queryset = Booking.objects.all().order_by("-booked_at")
        include_resource_uri = True
        resource_name = 'recent_bookings'
        allowed_methods = ['get']
        fields = ['ref', 'status','id', "activity"]

    def dehydrate(self, bundle):
        bundle.data['status_display'] = bundle.obj.get_status_display()
        bundle.data['who'] = bundle.obj.who
        bundle.data['when'] = bundle.obj.when
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what

        return bundle

class RequestedBookingsResource(ModelResource):
    #TODO: Only return own bookings
    client = fields.ToOneField(ClientResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)
    activity = fields.ToOneField(ActivityResource, "activity", full=True, blank=True, null=True)

    class Meta:
        queryset = Booking.objects.requested()
        include_resource_uri = True
        resource_name = 'requested_bookings'
        allowed_methods = ['get']
        fields = ['ref', 'requested_from','requested_to', 'studio','instrument',"activity", "status"]

    def dehydrate(self, bundle):
        bundle.data['status_display'] = bundle.obj.get_status_display()
        bundle.data['who'] = ''
        bundle.data['when'] = bundle.obj.when
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what
        bundle.data['activity'] = bundle.obj.activity.name

        return bundle

class AcceptedBookingsResource(ModelResource):
    #TODO: Only return own bookings

    client = fields.ToOneField(ClientResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)
    tuner = fields.ToOneField(UserResource, "tuner", full=True)


    class Meta:
        queryset = Booking.objects.filter(status="booked")
        include_resource_uri = True
        resource_name = 'booked_bookings'
        allowed_methods = ['get']
        fields = ['ref', 'booked_time','duration','client', 'studio','instrument', 'tuner']

    def dehydrate(self, bundle):

        bundle.data['booked_time'] = bundle.obj.booked_time
        bundle.data['who'] = ''
        bundle.data['when'] = bundle.obj.when
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what
        bundle.data['tuner'] = bundle.obj.tuner.get_full_name()
        return bundle

class BookingsToCompleteResource(AcceptedBookingsResource):

    class Meta:
        queryset = Booking.objects.to_complete()
        resource_name = 'bookings_to_complete'

class BookingsToPaidResource(AcceptedBookingsResource):

    class Meta:
        queryset = Booking.objects.completed()
        resource_name = 'bookings_to_paid'


class LogResource(ModelResource):
    """ calls to related
    /log/?format=json&booking__ref=ca9359
    """
    #booking = fields.ToOneField(BookingsResource, "booking", full=True)
    #created_by = fields.ToOneField(UserResource, "created_by", full=True)

    #TODO: Only return comments on booking where involved
    class Meta:
        queryset = Log.objects.all().select_related('customuser')
        include_resource_uri = False
        resource_name = 'log'
        limit = 100
        allowed_methods = ['post','get', 'option']
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'booking': ALL_WITH_RELATIONS,
            'created': ALL,
            'created_by': ALL_WITH_RELATIONS,
            'log_type': ALL,

        }

    def obj_create(self, bundle, request=None, **kwargs):

        try:
            booking = Booking.objects.get(ref = bundle.data['pk'])
        except Booking.DoesNotExist:
             raise BadRequest('Invalid Booking reference %s' % bundle.data['pk'])

        Log.objects.create(booking = booking,
                           comment = bundle.data['value'][0:254],
                           created_by = bundle.request.user)


        return None


    def get_object_list(self, request):
        '''could do this via tastypie but it would got and do calls for each foreign key
        '''
        base = super(LogResource, self).get_object_list(request)


        if request._get.has_key('client_id'):
            base =  base.filter(booking__client_id = request._get['client_id'])

        if request._get.has_key('user_id'):
            base =  base.filter(created_by_id = request._get['user_id'])


        if request._get.has_key('ref'):
            base = base.filter(booking__ref = request._get['ref'])



        return base


    def dehydrate(self, bundle):
        bundle.data['booking_url'] = bundle.obj.booking.get_absolute_url()
        bundle.data['booking_ref'] = bundle.obj.booking.ref
        bundle.data['long_heading'] = bundle.obj.booking.long_heading
        bundle.data['user_id'] = bundle.obj.created_by_id
        if hasattr(bundle.obj.created_by, 'gravatar'):
            bundle.data['gravatar'] = bundle.obj.created_by.gravatar
        else:
            bundle.data['gravatar'] = ""

        return bundle

class RecentBookingsCount(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'recent_bookings_count'
        allowed_methods = ['get',]
        object_class = SimpleObject

    def get_object_list(self, request):
        base = super(RecentBookingsCount, self).get_object_list(request)
        if request._get.has_key('client_id'):
            return base.filter(client_id = request._get['client_id'])
        else:
            return base
