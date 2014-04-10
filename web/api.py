import urlparse

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from tastypie import fields
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication, Authentication, BasicAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization, ReadOnlyAuthorization
from tastypie.exceptions import NotFound, BadRequest
from tastypie.paginator import Paginator
from tastypie.serializers import Serializer


from web.models import *

from django.contrib.auth import get_user_model
User = get_user_model()


'''
NOTE: TIMEZONE handling = model.py deals in timezone aware dates, the tempalates will automatically display local
datetimes.  In the API all times need to be converted to local.
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
        # for fullCalendar
        # see http://arshaw.com/fullcalendar/docs2/event_data/Event_Object/

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
        bundle.data['name'] = bundle.obj.get_full_name()

        return bundle

class StudioResource(ModelResource):
    class Meta:
        queryset = Studio.objects.all()
        include_resource_uri = False
        resource_name = 'studio'
        limit = 0
        allowed_methods = ['get']

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
        allowed_methods = ['get']
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
    client = fields.ToOneField(ClientResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)
    tuner = fields.ToOneField(UserResource, "tuner", full=True, blank=True, null=True)
    activity = fields.ToOneField(ActivityResource, "activity", full=True, blank=True, null=True)
    # dataset = fields.CharField(attribute="dataset", blank=True, null=True)

    class Meta:
        queryset = Booking.objects.all()
        include_resource_uri = True
        resource_name = 'bookings'
        allowed_methods = ['get']
        limit = 0
        fields = ['ref','requested_from','requested_to','studio','instrument', 'status']
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

        bundle.data['title'] = bundle.obj.long_heading

        bundle.data['start'] = timezone.localtime(bundle.obj.start_time)
        bundle.data['end'] = timezone.localtime(bundle.obj.end_time)
        bundle.data['status_display'] = bundle.obj.get_status_display()

        bundle.data['who'] = bundle.obj.who
        bundle.data['when'] = timezone.localtime(bundle.obj.when)
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what

        bundle.data['activity'] = bundle.obj.activity.name

        return bundle

    def get_object_list(self, request):
        base = super(BookingsResource, self).get_object_list(request)
        if request._get.has_key('dataset'):
            dataset = request._get.get('dataset')
            if dataset.lower() == "current":
                return base.current()
            elif dataset.lower() == "archived":
                return base.archived()

        else:
            return base


class MakeBookingResource(ModelResource):
    #TODO: Only return own bookings

    class Meta:
        queryset = Booking.objects.all()
        include_resource_uri = True
        resource_name = 'make_booking'
        allowed_methods = ['post']

class AcceptBookingResource(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'accept_booking'
        allowed_methods = ['post','put','get','options']
        include_resource_uri = False
        object_class = SimpleObject
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()


    def obj_create(self, bundle, request=None, **kwargs):

        ref = bundle.data['pk']
        tuner_id = bundle.data['value']
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)
            tuner = Tuner.objects.get(id=tuner_id)
            booking.book(tuner)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)
        except Tuner.DoesNotExist:
            raise BadRequest('Invalid Tuner id %s' % tuner_id)

        message = "Booking %s accepted by %s" % (ref, tuner.get_full_name())
        #TODO: This object is not being returned, it's not getting serialised for some reason
        return  None



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
        bundle.data['when'] = timezone.localtime(bundle.obj.when)
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
        bundle.data['when'] = timezone.localtime(bundle.obj.when)
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

        bundle.data['booked_time'] = timezone.localtime(bundle.obj.booked_time)
        bundle.data['who'] = ''
        bundle.data['when'] = timezone.localtime(bundle.obj.when)
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



class BookingCompleteResource(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'booking_complete'
        allowed_methods = ['post','option']
        object_class = SimpleObject
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()


    def obj_create(self, bundle, request=None, **kwargs):

        ref = bundle.data['ref']
        state = bundle.data['state']
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)


        if state == "true":
            booking.set_complete()
            message = "Booking %s set to Completed" % (ref, )
        else:
            booking.set_uncomplete()
            message = "Booking %s set back to Booked" % (ref, )

        #TODO: This object is not being returned, it's not getting serialised for some reason
        return  None

class BookingProviderPaidResource(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'booking_provider_paid'
        allowed_methods = ['post','option']
        object_class = SimpleObject
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()


    def obj_create(self, bundle, request=None, **kwargs):

        ref = bundle.data['ref']
        state = bundle.data['state']
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)


        if state == "true":
            booking.set_provider_paid()
            message = _("Booking %s tuner paid") % (ref, )
        else:
            booking.set_provider_unpaid()
            message = _("Booking %s tuner unpaid") % (ref, )


        return  None

class BookingClientPaidResource(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'booking_client_paid'
        allowed_methods = ['post','option']
        object_class = SimpleObject
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()


    def obj_create(self, bundle, request=None, **kwargs):

        ref = bundle.data['ref']
        state = bundle.data['state']
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)


        if state == "true":
            booking.set_client_paid()
            message = _("Booking %s client paid") % (ref, )
        else:
            booking.set_client_unpaid()

            message = _("Booking %s client unpaid") % (ref, )

        return  None

class BookingCancelResource(Resource):

    class Meta:
        include_resource_uri = True
        resource_name = 'booking_cancel'
        allowed_methods = ['post','option']
        object_class = SimpleObject
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()


    def obj_create(self, bundle, request=None, **kwargs):

        ref = bundle.data['ref']
        me = bundle.request.user

        try:
            booking = Booking.objects.get(ref=ref)

        except Booking.DoesNotExist:
            raise BadRequest('Invalid Booking reference %s' % ref)



        booking.cancel(me)
        message = _("Booking %s cancelled") % (ref, )

        return  None

class LogResource(ModelResource):

    created_by = fields.ToOneField(UserResource, "created_by", full=True)

    #TODO: Only return comments on booking where involved
    class Meta:
        queryset = Log.objects.all()
        include_resource_uri = False
        resource_name = 'log'
        limit = 100
        allowed_methods = ['post','get', 'option']
        serializer = urlencodeSerializer()
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'booking_id': ['exact', ],
            'ref': ['exact']
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
        base = super(LogResource, self).get_object_list(request)
        if request._get.has_key('ref'):
            return base.filter(booking__ref = request._get['ref'])
        else:
            return base


    def dehydrate(self, bundle):
        bundle.data['created'] = timezone.localtime(bundle.obj.created)
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
