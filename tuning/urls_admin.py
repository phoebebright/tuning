
from django.conf.urls import patterns, include, url

from web.views import BookingCreate, BookingUpdate, BookingDelete, BookingDetailView, BookingCompleteView

urlpatterns = patterns('web.views',
                        url(r'^$','dashboard' ,name="dashboard"),
                        url(r'^calendar', 'calendar', name="calendar"),
                        url(r'^booking/assign/$', 'assign_tuner', name="assign_tuner"),
                        url(r'^booking/to_completed/$', 'to_completed', name="to_completed"),
                        url(r'^booking/to_paid/$', 'to_paid', name="to_paid"),
                        url(r'^bookings/$', 'bookings_list', name="bookings_list"),

                        )
urlpatterns += patterns('',
                       #login required
                        url(r'booking/add/$', BookingCreate.as_view(), name='booking_add'),
                        url(r'booking/(?P<pk>\d+)/delete/$', BookingDelete.as_view(), name='booking_delete'),
                        url(r'booking/(?P<pk>\d+)/$', BookingDetailView.as_view(), name='booking-detail'),
                        url(r'booking/(?P<ref>\w+)/$', BookingDetailView.as_view(), name='booking-detail'),
                        url(r'booking/complete/(?P<pk>\d+)/$', BookingCompleteView.as_view(), name='booking-complete'),

                        )
