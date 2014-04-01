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
from web.views import BookingCreate, BookingUpdate, BookingDelete, BookingDetailView

v1_api = Api(api_name='v1')

v1_api.register(ClientResource())
v1_api.register(ProviderResource())
v1_api.register(TunerResource())
v1_api.register(ClientMinResource())
v1_api.register(RequestBookingResource())
v1_api.register(BookingsResource())
v1_api.register(AcceptBookingResource())
v1_api.register(RecentBookingsResource())
v1_api.register(RequestedBookingsResource())
v1_api.register(AcceptedBookingsResource())
v1_api.register(MakeBookingResource())
v1_api.register(StudioResource())
v1_api.register(InstrumentResource())


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

urlpatterns = patterns('',
                       url(r'^api/', include(v1_api.urls)),

                       url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', name="logout"),
                       url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', name="password_reset"),
                       url(r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'registration/password_reset_done.html'}, name="password_reset_done"),
                       url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
                       url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete', name="password_reset_complete"),
                       url(r'^index.html$', DirectTemplateView.as_view(template_name='index.html'),  name="index"),
                       url(r'^admin/', include(admin.site.urls)),

                       #login required
                       url(r'^$', login_required(BookingCreate.as_view()), name='booking_add'),
                       url(r'booking/add/$', login_required(BookingCreate.as_view()), name='booking_add'),
                       url(r'booking/(?P<pk>\d+)/$', login_required(BookingUpdate.as_view()), name='booking_update'),
                       url(r'booking/(?P<pk>\d+)/delete/$', login_required(BookingDelete.as_view()), name='booking_delete'),
                       url(r'booking/(?P<slug>[-_\w]+)/$', login_required(BookingDetailView.as_view()), name='booking-detail'),  # not used?
                       #TODO: booking-detail and booking-list
                       )+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


urlpatterns += patterns('web.views',
                        url(r'^dashboard', 'dashboard', name="dashboard"),
                        )

if settings.DEBUG:
    urlpatterns += patterns('',
                            (r'^test_data$', 'web.management.test_data.test_data'),
                            (r'^apis$', DirectTemplateView.as_view(template_name='apis.html')),

                            )