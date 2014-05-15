from django.conf.urls import patterns, include, url

from django.contrib import admin

#TODO: this can be returned from facebook via django-facebook http://gmd.pagekite.me/?fb_error_or_cancel=1#_=_
import os.path

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required, user_passes_test

'''
API Stuff
'''

from tastypie.api import Api
from web.api import *
from web.views import BookingCreate, BookingUpdate, BookingDelete, BookingDetailView, BookingCompleteView
from libs.utils import required

v1_api = Api(api_name='v1')

v1_api.register(AcceptBookingResource())
v1_api.register(AcceptedBookingsResource())
v1_api.register(ActivityResource())
v1_api.register(BookerResource())
v1_api.register(BookingActivityResource())
v1_api.register(BookingBookerResource())
v1_api.register(BookingCancelResource())
v1_api.register(BookingClientPaidResource())
v1_api.register(BookingClientrefResource())
v1_api.register(BookingCompleteResource())
v1_api.register(BookingCreateResource())
v1_api.register(BookingDeadlineResource())
v1_api.register(BookingDeleteResource())
v1_api.register(BookingDurationResource())
v1_api.register(BookingInstrumentResource())
v1_api.register(BookingProviderPaidResource())
v1_api.register(BookingsCalendarResource())
v1_api.register(BookingsFullResource())
v1_api.register(BookingsResource())
v1_api.register(BookingPriceResource())
v1_api.register(BookingsToCompleteResource())
v1_api.register(BookingsToPaidResource())
v1_api.register(BookingStudioResource())
v1_api.register(BookingTunerResource())
v1_api.register(ClientMinResource())
v1_api.register(ClientResource())
v1_api.register(InstrumentResource())
v1_api.register(LogResource())
v1_api.register(MakeBookingResource())
v1_api.register(ProviderResource())
v1_api.register(RecentBookingsResource())
v1_api.register(RequestBookingResource())
v1_api.register(RequestedBookingsResource())
v1_api.register(StudioResource())
v1_api.register(TunerResource())


'''
direct to template
'''
class DirectTemplateView(TemplateView):
    extra_context = None
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context


admin.autodiscover()

def is_admin(user):
    if user and user.is_admin:
        return user.is_staff
    else:
        return False

def is_booker(user):
    if user and user.is_booker:
        return True
    else:
        return False

def is_tuner(user):
    if user and user.is_tuner:
        return True
    else:
        return False




urlpatterns = patterns('',
                       url(r'^api/', include(v1_api.urls)),

                       url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),
                       url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', name="password_reset"),
                       url(r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'registration/password_reset_done.html'}, name="password_reset_done"),
                       url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete', name="password_reset_complete"),
                       #                       url(r'^index.html$', DirectTemplateView.as_view(template_name='index.html'),  name="index"),


                       url(r'^admin/', include(admin.site.urls)),

                       ) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# urlpatterns += required(
#     is_admin,
#     patterns('',
#         (r'^private/', include('admin.urls'))
#     )
# )

urlpatterns += patterns('web.views',
                        url(r'^$','dashboard' ,name="dashboard"),
                        url(r'^calendar', 'calendar', name="calendar"),
                        url(r'^booking/add/$', 'bookings_add', name='booking_add'),
                        url(r'^booking/add/(?P<client_id>\d+)/$', 'bookings_add', name='booking_add_client'),
                        url(r'^booking/add/(?P<client_id>\d+)/(?P<deadline>\d+)/$', 'bookings_add', name='booking_add_client_deadline'),
                        url(r'^booking/assign/$', 'assign_tuner', name="assign_tuner"),
                        url(r'^booking/to_completed/$', 'to_completed', name="to_completed"),
                        url(r'^booking/to_paid/$', 'to_paid', name="to_paid"),
                        url(r'^bookings/$', 'bookings_list', name="bookings_list"),
                        url(r'^booking/template/(?P<booking_ref>\w+)/$', 'render_booking_template', name="render_booking_template"),
                        url(r'^webmaster/$', 'webmaster', name='webmaster'),
                        url(r'^ping/$', 'ping', name='ping'),
                        )
urlpatterns += patterns('',
                       #login required
                       #url(r'booking/add/$', login_required(BookingCreate.as_view()), name='booking_add'),
                       url(r'booking/(?P<pk>\d+)/delete/$', login_required(BookingDelete.as_view()), name='booking_delete'),
                       url(r'booking/(?P<pk>\d+)/$', login_required(BookingDetailView.as_view()), name='booking-detail'),
                       url(r'booking/(?P<ref>\w+)/$', login_required(BookingDetailView.as_view()), name='booking-detail'),
                       url(r'booking/complete/(?P<pk>\d+)/$', login_required(BookingCompleteView.as_view()), name='booking-complete'),
                       url(r'booking/request_tuner/(?P<booking_ref>\w+)/$', 'request_another_tuner', name='booking-request-tuner'),


)





if settings.DEBUG:
    urlpatterns += patterns('',
                            (r'^test_data$', 'web.management.test_data.test_data'),
                            (r'^apis$', DirectTemplateView.as_view(template_name='apis.html')),

                            )