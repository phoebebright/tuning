from django.db import IntegrityError
from django.core.exceptions import ValidationError


from tastypie import fields
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication, Authentication, BasicAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization, ReadOnlyAuthorization
from tastypie.exceptions import NotFound, BadRequest
from tastypie.paginator import Paginator

from web.models import *

from django.contrib.auth import get_user_model
User = get_user_model()


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

class BookingsResource(ModelResource):
    #TODO: Only return own bookings

    class Meta:
        queryset = Booking.objects.all()
        include_resource_uri = True
        resource_name = 'bookings'
        allowed_methods = ['get']
        limit = 0
        fields = ['requested_from','requested_to','location','instrument', 'status']
        filtering = {
            'client_id': ('exact',),
            'status': ('exact',),
        }
        #
        # authorization = Authorization()
        # authentication = GMDAuthentication()

    def dehydrate(self, bundle):
        # for fullCalendar
        # see http://arshaw.com/fullcalendar/docs2/event_data/Event_Object/

        bundle.data['title'] = "%s in %s" % (bundle.obj.instrument, bundle.obj.location)

        bundle.data['start'] = bundle.obj.start_time
        bundle.data['end'] = bundle.obj.end_time
        bundle.data['className'] = bundle.obj.status

        bundle.data['allDay'] = "false"


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


class OrganisationResource(ModelResource):
    class Meta:
        queryset = Organisation.objects.all()
        include_resource_uri = False
        resource_name = 'organisations'
        limit = 0
        allowed_methods = ['get']
        filtering = {
            'org_type': ['exact', ]
        }
class ClientResource(ModelResource):
    class Meta:
        queryset = Organisation.objects.filter(org_type="client")
        include_resource_uri = False
        resource_name = 'clients'
        limit = 0
        allowed_methods = ['get']

class TunerResource(ModelResource):
    class Meta:
        queryset = Organisation.objects.filter(org_type="provider")
        include_resource_uri = False
        resource_name = 'tuners'
        limit = 0
        allowed_methods = ['get']
        
        
class OrganisationMinResource(ModelResource):
    class Meta:
        queryset = Organisation.objects.all()
        include_resource_uri = False
        fields = ['id', 'name']
        limit = 0
        resource_name = 'orgs'
        allowed_methods = ['get']
        filtering = {
            'org_type': ['exact', ]
        }

class LocationResource(ModelResource):
    organisation = fields.ToOneField(OrganisationResource, "organisation", full=False)

    class Meta:
        queryset = Location.objects.all()
        include_resource_uri = False
        resource_name = 'locations'
        limit = 0
        allowed_methods = ['get']
        filtering = {
            'organisation_id': ['exact', ]
        }

    def get_object_list(self, request):
        base = super(LocationResource, self).get_object_list(request)
        if request._get.has_key('organisation_id'):
            return base.filter(organisation_id = request._get['organisation_id'])
        else:
            return base

class InstrumentResource(ModelResource):
    organisation = fields.ToOneField(OrganisationResource, "organisation", full=False)

    class Meta:
        queryset = Instrument.objects.all()
        include_resource_uri = False
        resource_name = 'instruments'
        limit = 0
        allowed_methods = ['get']
        filtering = {
            'organisation_id': ['exact', ]
        }

    def get_object_list(self, request):
        base = super(InstrumentResource, self).get_object_list(request)
        if request._get.has_key('organisation_id'):
            return base.filter(organisation_id = request._get['organisation_id'])
        else:
            return base



class MakeBookingResource(ModelResource):
    #TODO: Only return own bookings

    class Meta:
        queryset = Booking.objects.all()
        include_resource_uri = True
        resource_name = 'make_booking'
        allowed_methods = ['post']


class RecentBookingsResource(ModelResource):
    #TODO: Only return own bookings
    client = fields.ToOneField(OrganisationResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)

    class Meta:
        queryset = Booking.objects.all().order_by("-booked_at")
        include_resource_uri = True
        resource_name = 'recent_bookings'
        allowed_methods = ['get']
        fields = ['ref', 'status','id']

    def dehydrate(self, bundle):
        bundle.data['status'] = bundle.obj.get_status_display()
        bundle.data['who'] = bundle.obj.who
        bundle.data['when'] = bundle.obj.when
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what

        return bundle

class RequestedBookingsResource(ModelResource):
    #TODO: Only return own bookings
    client = fields.ToOneField(OrganisationResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)

    class Meta:
        queryset = Booking.objects.requested()
        include_resource_uri = True
        resource_name = 'requested_bookings'
        allowed_methods = ['get']
        fields = ['ref', 'requested_from','requested_to', 'location','instrument']

    def dehydrate(self, bundle):
        bundle.data['status'] = bundle.obj.get_status_display()
        bundle.data['who'] = ''
        bundle.data['when'] = bundle.obj.when
        bundle.data['where'] = bundle.obj.where
        bundle.data['what'] = bundle.obj.what

        return bundle

class AcceptedBookingsResource(ModelResource):
    #TODO: Only return own bookings

    client = fields.ToOneField(OrganisationResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)
    provider = fields.ToOneField(UserResource, "provider", full=True)


    class Meta:
        queryset = Booking.objects.filter(status="booked")
        include_resource_uri = True
        resource_name = 'booked_bookings'
        allowed_methods = ['get']
        fields = ['booked_time','duration','client', 'location','instrument']
