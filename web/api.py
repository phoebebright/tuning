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
        include_resource_uri = False
        list_allowed_methods = ['get', ]
        detail_allowed_methods = ['get',]


class OrganisationResource(ModelResource):
    class Meta:
        queryset = Organisation.objects.all()
        include_resource_uri = False
        resource_name = 'organisations'
        allowed_methods = ['get']




class RequestedBookingsResource(ModelResource):
    #TODO: Only return own bookings
    client = fields.ToOneField(OrganisationResource, "client", full=True)
    booker = fields.ToOneField(UserResource, "booker", full=True)

    class Meta:
        queryset = Booking.objects.filter(status="asked")
        include_resource_uri = True
        resource_name = 'requested_bookings'
        allowed_methods = ['get']
        fields = ['requested_from','requested_to', 'location','instrument']

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
