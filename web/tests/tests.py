from django.test import TestCase
from django.db import connection

from django.test import Client
from django import template
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from web.models import *
from web.exceptions import *
from web.management.test_data import *

from django.contrib.auth import get_user_model
User = get_user_model()

from django.conf import settings

from datetime import date, timedelta, time

# faketime allows the actual date to be set in the future past - for testing can be useful
from libs.faketime import now
NOW = now()
TODAY = NOW.date()
TODAY_START = make_time(TODAY, "start")
TODAY_END = make_time(TODAY, "end")
YESTERDAY = TODAY - timedelta(days = 1)
TOMORROW = TODAY + timedelta(days = 1)


def list_orgs():
    txt = "Organisations\n"
    for item in Organisation.objects.all():
            txt +=  "%30s | %20s  \n" % (item.name,item.id)

    return txt





class BookingTest(TestCase):
    """
    test booking process
    """

    def setUp(self):

        base_data()


        
        # get organisations
        self.o1=Organisation.objects.get(name="Recording Studio A")
        self.o2=Organisation.objects.get(name="Recording Studio B")
        self.o3=Organisation.objects.get(name="Private House")
        self.t1=Organisation.objects.get(name="Tuner A")
        self.t2=Organisation.objects.get(name="Tuner B")
        self.t3=Organisation.objects.get(name="Tuner C")
        self.t4=Organisation.objects.get(name="Tuner D")
        self.s=Organisation.objects.get(name="System")
        self.tst=Organisation.objects.get(name="Test Org")

    
        # get users

        self.freda = User.objects.get(username='fredA')
        self.jima = User.objects.get(username='jimA')
        self.maryb = User.objects.get(username='maryB')
        self.janeph = User.objects.get(username='janePH')
        self.matt = User.objects.get(username='matt')
        self.mark = User.objects.get(username='mark')
        self.luke = User.objects.get(username='luke')
        self.john = User.objects.get(username='john')
        self.testera = User.objects.get(username='testera')
        self.testerb = User.objects.get(username='testerb')
        self.ajs = User.objects.get(username='ajs')

        # locations
        self.sr = Location.objects.get(name="Studio Red")
        self.sb = Location.objects.get(name="Studio Blue")
        self.sy = Location.objects.get(name="Studio Yellow")
        self.sg = Location.objects.get(name="Studio Green")
        self.so = Location.objects.get(name="Studio Orange")
        self.s1 = Location.objects.get(name="Studio 1")
        self.s2 = Location.objects.get(name="Studio 2")


        # Instruments
        self.i1 = Instrument.objects.get(name="Steinway Grand")
        self.i2 = Instrument.objects.get(name="Steinway Upright")
        self.i3 = Instrument.objects.get(name="Fortepiano")
        self.i4 = Instrument.objects.get(name="Harpsicord")
        self.i5 = Instrument.objects.get(name="Grand")
        self.i6 = Instrument.objects.get(name="Upright")

    def test_user_properties(self):

        self.assertTrue(self.tst.is_test)
        self.assertTrue(self.testera.is_test)
        self.assertFalse(self.o1.is_test)
        self.assertFalse(self.matt.is_test)

        self.assertTrue(self.freda.is_client)
        self.assertFalse(self.freda.is_provider)
        self.assertFalse(self.freda.is_system)

        self.assertFalse(self.matt.is_client)
        self.assertTrue(self.matt.is_provider)
        self.assertFalse(self.matt.is_system)

        self.assertFalse(self.ajs.is_client)
        self.assertFalse(self.ajs.is_provider)
        self.assertTrue(self.ajs.is_system)

    def test_user_querysets(self):

        book1 = self.freda.request_booking(when=TOMORROW)

        self.assertEqual(Booking.objects.mine(self.freda).count(), 1)
        self.assertEqual(Booking.objects.mine(self.matt).count(), 0)

        #TODO: Fails
        #self.assertRaises(InvalidQueryset, Booking.objects.mine(self.ajs).count())


        # check active flag and client queryset
        self.assertEqual(Organisation.objects.clients().count(), 4)
        self.o2.active = False
        self.o2.save()
        self.assertEqual(Organisation.objects.clients().count(), 3)



    def test_make_booking(self):


        # test fails

        # can't book in the past

        self.assertRaises(PastDateException, self.freda.request_booking, when=YESTERDAY)
        self.assertRaises(PastDateException, self.freda.request_booking, when=datetime.combine(YESTERDAY, time(12,00)))
        self.assertRaises(DeadlineBeforeBookingException, self.freda.request_booking,
                          when=datetime.combine(TODAY, time(12,00)),
                          deadline=YESTERDAY)

        #TODO: Test unique ref not being unique - should generate another ref and try again

        # test passes
        self.assertEqual(self.freda.requested_bookings.count(),0)
        book1 = self.freda.request_booking(when=TODAY)
        book1a = Booking.objects.get(id=book1.id)
        self.assertEqual(self.freda.requested_bookings.count(),1)

        # populated fields
        self.assertEqual(book1.status, BOOKING_REQUESTED)
        self.assertEqual(book1.booker, self.freda)
        self.assertEqual(book1.client, self.o1)
        self.assertEqual(roundTime(book1.requested_at, 120), roundTime(NOW, 120))  # within 2 seconds
        self.assertEqual(book1.requested_from, TODAY_START)
        self.assertEqual(book1.requested_to, TODAY_END)
        self.assertIsNotNone(book1.ref)

        # unpopulated fields
        self.assertIsNone(book1.provider)
        self.assertIsNone(book1.completed_at)
        self.assertIsNone(book1.cancelled_at)
        self.assertIsNone(book1.paid_client_at)
        self.assertIsNone(book1.paid_provider)
        self.assertIsNone(book1.booked_time)
        self.assertIsNone(book1.location)
        self.assertIsNone(book1.instrument)
        self.assertIsNone(book1.deadline)
        self.assertIsNone(book1.client_ref)
        self.assertIsNone(book1.comments)

        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))

        book3 = self.jima.request_booking(when=(TODAY + timedelta(days = 4)), client_ref="Bono", what=self.i1, where=self.sr)
        self.assertEqual(book3.instrument, self.i1)
        self.assertEqual(book3.location, self.sr)

        # specify all fields
        starts = datetime.combine(TOMORROW, time(11,00))
        ends = datetime.combine(TOMORROW, time(14,15))
        deadline = datetime.combine(TOMORROW, time(15,00))
        book4 = Booking.create_booking(self.jima, when=(starts, ends), deadline=deadline, where=self.sr, what=self.i1, client_ref="testref", comments="fulltest" )
        self.assertEqual(book4.status, BOOKING_REQUESTED)
        self.assertEqual(book4.booker, self.jima)
        self.assertEqual(book4.client, self.o1)
        self.assertEqual(roundTime(book4.requested_at, 120), roundTime(NOW, 120))  # within 2 seconds
        self.assertEqual(book4.requested_from, starts)
        self.assertEqual(book4.requested_to, ends)
        self.assertEqual(book4.client_ref, "testref")
        self.assertEqual(book4.location, self.sr)
        self.assertEqual(book4.instrument, self.i1)
        self.assertEqual(book4.comments, "fulltest")
        self.assertEqual(book4.deadline, deadline)
        self.assertIsNotNone(book4.ref)

    def test_book(self):

        self.assertEqual(self.jima.accepted_bookings.count(),0)

        # accept booking from booking object
        book1 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        book1.book(provider=self.matt, start_time=datetime.combine(TOMORROW, time(12,15)))

        self.assertEqual(book1.status, BOOKING_BOOKED)
        self.assertEqual(book1.provider, self.matt)
        self.assertEqual(roundTime(book1.booked_time, 120), roundTime(datetime.combine(TOMORROW, time(12,15)), 120))  # within 2 seconds
        self.assertEqual(roundTime(book1.booked_at, 120), roundTime(NOW, 120))  # within 2 seconds

        self.assertEqual(self.matt.accepted_bookings.count(),1)


        # accept booking from user
        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        self.assertEqual(self.matt.accepted_bookings.count(),1)

        book2 = self.matt.accept_booking(book2.ref, start_time=datetime.combine(TOMORROW, time(12,15)))

        self.assertEqual(book2.status, BOOKING_BOOKED)
        self.assertEqual(book2.provider, self.matt)
        self.assertEqual(roundTime(book2.booked_time, 120), roundTime(datetime.combine(TOMORROW, time(12,15)), 120))  # within 2 seconds
        self.assertEqual(roundTime(book2.booked_at, 120), roundTime(NOW, 120))  # within 2 seconds

        self.assertEqual(self.matt.accepted_bookings.count(),2)

    def test_cancel(self):

        # bookings not accepted
        book1 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        book1.cancel(self.jima)

        book1 = Booking.objects.get(id=book1.id)
        self.assertEqual(book1.status, BOOKING_ARCHIVED)
        self.assertEqual(book1.cancelled_at, roundTime(NOW, 120))

        # fully booked
        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        self.assertEqual(self.matt.accepted_bookings.count(),1)
        book2 = self.matt.accept_booking(book2.ref, start_time=datetime.combine(TOMORROW, time(12,15)))
        book2.cancel(self.jima)

        book2 = Booking.objects.get(id=book2.id)
        self.assertEqual(book2.status, BOOKING_ARCHIVED)
        self.assertEqual(book2.cancelled_at, roundTime(NOW, 120))


def roundTime(dt=None, roundTo=60):

   """Round a datetime object to any time laps in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
   """
   if dt == None :
        return None
   seconds = (dt - dt.min).seconds
   # // is a floor division, not a comment on following line:
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + timedelta(0,rounding-seconds,-dt.microsecond)
