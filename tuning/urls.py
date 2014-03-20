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

v1_api = Api(api_name='v1')
v1_api.register(OrganisationResource())
v1_api.register(RequestBookingResource())
v1_api.register(BookingsResource())
v1_api.register(RequestedBookingsResource())
v1_api.register(AcceptedBookingsResource())


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
    url(r'^$', DirectTemplateView.as_view(template_name='index.html'),  name="home"),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
            (r'^test_data$', 'web.management.test_data.test_data'),
    )