from django.test import TestCase
from django.db import connection

from django.test import Client
from django import template
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone

from web.models import *
from web.exceptions import *
from web.management.test_data import *

from django.contrib.auth import get_user_model
User = get_user_model()

from django.conf import settings

from datetime import date, timedelta, time
from django.utils.timezone import utc



# # faketime allows the actual date to be set in the future past - for testing can be useful
# from libs.faketime import now
# NOW = now()
NOW = datetime.utcnow().replace(tzinfo=utc)
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


'''

NOTE - not all tests pass when checking for bookings in the past
'''


class BookingTest(TestCase):
    """
    test booking process
    """

    def setUp(self):

        base_data()


        
        # get organisations
        self.o1=Client.objects.get(name="Recording Studio A")
        self.o2=Client.objects.get(name="Recording Studio B")
        self.o3=Client.objects.get(name="Private House")
        self.t1=Provider.objects.get(name="Tuner A")
        self.t3=Provider.objects.get(name="Tuner C")
        self.t4=Provider.objects.get(name="Tuner D")
        self.tstc=Client.objects.get(name="Test Client")
        self.tstp=Provider.objects.get(name="Test Provider")

    
        # get users

        self.freda = Booker.objects.get(username='fredA')
        self.jima = Booker.objects.get(username='jimA')
        self.maryb = Booker.objects.get(username='maryB')
        self.janeph = Booker.objects.get(username='janePH')
        self.matt = Tuner.objects.get(username='matt')
        self.mark = Tuner.objects.get(username='mark')
        self.luke = Tuner.objects.get(username='luke')
        self.john = Tuner.objects.get(username='john')
        self.testera = Booker.objects.get(username='testera')
        self.testerb = Tuner.objects.get(username='testerb')
        self.ajs = User.objects.get(username='ajs')

        # studios
        self.sr = Studio.objects.get(name="Studio Red")
        self.sb = Studio.objects.get(name="Studio Blue")
        self.sy = Studio.objects.get(name="Studio Yellow")
        self.sg = Studio.objects.get(name="Studio Green")
        self.so = Studio.objects.get(name="Studio Orange")
        self.s1 = Studio.objects.get(name="Studio 1")
        self.s2 = Studio.objects.get(name="Studio 2")


        # Instruments
        self.i1 = Instrument.objects.get(name="Steinway Grand")
        self.i2 = Instrument.objects.get(name="Steinway Upright")
        self.i3 = Instrument.objects.get(name="Fortepiano")
        self.i4 = Instrument.objects.get(name="Harpsicord")
        self.i5 = Instrument.objects.get(name="Grand")
        self.i6 = Instrument.objects.get(name="Upright")


        #get activities
        self.a1 = Activity.objects.get(name="Tuning")
        self.a2 = Activity.objects.get(name="Repair")


    def test_refs(self):
        """
        a temporary ref is created when a new bookings is being added from a form in order to be able
        to add comments (comments needs a booking ref)
        """

        temp_ref = Booking.create_temp_ref()
        self.assertEqual(len(temp_ref), 6)

        temp_ref2 = Booking.create_temp_ref()
        self.assertNotEqual(temp_ref, temp_ref2)


        """
        if a booking is created without a studio and with a ref, then assume the ref is a temporary one and
        replace with a proper one
        """

        book = Booking.objects.create(ref = Booking.create_temp_ref())

        self.assertTrue(book.has_temp_ref)

        book.client = self.o1
        book.studio = self.s1
        book.save()

        self.assertTrue(book.has_temp_ref)

        book.deadline = TOMORROW
        book.save()

        # has the data to create a permanent ref
        self.assertFalse(book.has_temp_ref)


        book2 = Booking.objects.create(
        client = self.o1,
        studio = self.s1,
        deadline = TOMORROW)

        self.assertNotEqual(book.ref, book2.ref)
        self.assertEqual(book.ref[:8], book2.ref[:8])
        self.assertEqual(book.ref[-1], 'a')
        self.assertEqual(book2.ref[-1], 'b')


    def test_make_booking(self):


        # test fails

        # can't book in the past

        self.assertRaises(PastDateException, self.freda.request_booking, when=YESTERDAY)
        self.assertRaises(PastDateException, self.freda.request_booking, when=datetime.combine(YESTERDAY, time(12,00)))
        self.assertRaises(DeadlineBeforeBookingException, self.freda.request_booking,
                          when=datetime.combine(TODAY, time(23,00)),
                          deadline=YESTERDAY)

        #TODO: Test unique ref not being unique - should generate another ref and try again

        # test passes
        self.assertEqual(Booking.objects.mine(self.freda).count(),0)
        book1 = self.freda.request_booking(when=TODAY)
        book1a = Booking.objects.get(id=book1.id)
        self.assertEqual(Booking.objects.mine(self.freda).count(),1)

        # populated fields
        self.assertEqual(book1.status, BOOKING_REQUESTED)
        self.assertEqual(book1.activity, self.a1)
        self.assertEqual(book1.booker, self.freda)
        self.assertEqual(book1.client, self.o1)
        self.assertEqual(roundTime(book1.requested_at, 120), roundTime(NOW, 120))  # within 2 seconds
        self.assertEqual(book1.requested_from, TODAY_START)
        self.assertEqual(book1.requested_to, TODAY_END)
        self.assertIsNotNone(book1.ref)

        # unpopulated fields
        self.assertIsNone(book1.tuner)
        self.assertIsNone(book1.completed_at)
        self.assertIsNone(book1.cancelled_at)
        self.assertIsNone(book1.paid_client_at)
        self.assertIsNone(book1.paid_provider_at)
        self.assertIsNone(book1.booked_time)
        self.assertIsNone(book1.studio)
        self.assertIsNone(book1.instrument)
        self.assertIsNone(book1.deadline)
        self.assertIsNone(book1.client_ref)

        #TODO: test comments

        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))

        book3 = self.jima.request_booking(when=(TODAY + timedelta(days = 4)), client_ref="Bono", what=self.i1, where=self.sr)
        self.assertEqual(book3.instrument, self.i1)
        self.assertEqual(book3.studio, self.sr)

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
        self.assertEqual(book4.studio, self.sr)
        self.assertEqual(book4.instrument, self.i1)
        self.assertEqual(book4.deadline, deadline)
        self.assertIsNotNone(book4.ref)

    def test_book(self):


        # accept booking from booking object
        book1 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        book1.book(tuner=self.matt, start_time=datetime.combine(TOMORROW, time(12,15)))

        self.assertEqual(book1.status, BOOKING_BOOKED)
        self.assertEqual(book1.tuner, self.matt)
        self.assertEqual(roundTime(book1.booked_time, 120), roundTime(datetime.combine(TOMORROW, time(12,15)), 120))  # within 2 seconds
        self.assertEqual(roundTime(book1.booked_at, 120), roundTime(NOW, 120))  # within 2 seconds

        self.assertEqual(self.matt.accepted_bookings.count(),1)


        # accept booking from user
        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        self.assertEqual(self.matt.accepted_bookings.count(),1)

        book2 = self.matt.accept_booking(book2.ref, start_time=datetime.combine(TOMORROW, time(12,15)))

        self.assertEqual(book2.status, BOOKING_BOOKED)
        self.assertEqual(book2.tuner, self.matt)
        self.assertEqual(roundTime(book2.booked_time, 120), roundTime(datetime.combine(TOMORROW, time(12,15)), 120))  # within 2 seconds
        self.assertEqual(roundTime(book2.booked_at, 120), roundTime(NOW, 120))  # within 2 seconds

        self.assertEqual(self.matt.accepted_bookings.count(),2)

    def test_cancel(self):

        # bookings not accepted
        book1 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        book1.cancel(self.jima)

        book1 = Booking.objects.get(id=book1.id)
        self.assertEqual(book1.status, BOOKING_ARCHIVED)
        self.assertEqual(roundTime(book1.cancelled_at, 120), roundTime(NOW, 120))

        # fully booked
        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        self.assertEqual(self.matt.accepted_bookings.count(),1)
        book2 = self.matt.accept_booking(book2.ref, start_time=datetime.combine(TOMORROW, time(12,15)))
        self.assertEqual(self.matt.accepted_bookings.count(),2)
        book2.cancel(self.jima)
        self.assertEqual(self.matt.accepted_bookings.count(),1)

        book2 = Booking.objects.get(id=book2.id)
        self.assertEqual(book2.status, BOOKING_ARCHIVED)
        self.assertEqual(book2.cancelled_at, roundTime(NOW, 120))



    def test_user_querysets(self):

        book1 = self.freda.request_booking(when=TOMORROW)

        self.assertEqual(Booking.objects.mine(self.freda).count(), 1)
        self.assertEqual(Booking.objects.mine(self.matt).count(), 0)

        #TODO: Fails
        #self.assertRaises(InvalidQueryset, Booking.objects.mine(self.ajs).count())


        # check active flag and client queryset
        self.assertEqual(Client.objects.active().count(), 4)
        self.o2.active = False
        self.o2.save()
        self.assertEqual(Client.objects.active().count(), 3)

    def test_booking_querysets(self):
        # TODO: Better test of to_complete

        self.assertEqual(Booking.objects.current().count(), 0)
        self.assertEqual(Booking.objects.requested().count(), 0)
        self.assertEqual(Booking.objects.booked().count(), 0)
        self.assertEqual(Booking.objects.set_complete().count(), 0)
        self.assertEqual(Booking.objects.archived().count(), 0)
        self.assertEqual(Booking.objects.to_complete().count(), 0)

        book1 = self.jima.request_booking(when=YESTERDAY, client_ref="Jam", deadline=YESTERDAY)
        self.assertEqual(Booking.objects.current().count(), 1)
        self.assertEqual(Booking.objects.requested().count(), 1)
        self.assertEqual(Booking.objects.booked().count(), 0)
        self.assertEqual(Booking.objects.set_complete().count(), 0)
        self.assertEqual(Booking.objects.archived().count(), 0)
        self.assertEqual(Booking.objects.to_complete().count(), 0)

        # to complete set as this booking was yesterday
        book1.book(tuner=self.matt, start_time=YESTERDAY)
        self.assertEqual(Booking.objects.current().count(), 1)
        self.assertEqual(Booking.objects.requested().count(), 0)
        self.assertEqual(Booking.objects.booked().count(), 1)
        self.assertEqual(Booking.objects.set_complete().count(), 0)
        self.assertEqual(Booking.objects.archived().count(), 0)
        self.assertEqual(Booking.objects.to_complete().count(), 1)

        # the to_complete only pulls bookings that are past their start time so add another to differentiate
        book2 = self.jima.request_booking(when=TOMORROW, client_ref="Jam2", deadline=TOMORROW)
        book2.book(tuner=self.matt)


        self.assertEqual(Booking.objects.current().count(), 2)
        self.assertEqual(Booking.objects.requested().count(), 0)
        self.assertEqual(Booking.objects.booked().count(), 2)
        self.assertEqual(Booking.objects.set_complete().count(), 0)
        self.assertEqual(Booking.objects.archived().count(), 0)
        self.assertEqual(Booking.objects.to_complete().count(), 1)


    def test_user_properties(self):

        self.assertEqual(self.freda.client, self.o1)
        self.assertEqual(self.matt.provider, self.t1)

        self.assertTrue(self.tstc.is_test)
        self.assertTrue(self.testera.is_test)
        self.assertFalse(self.o1.is_test)
        self.assertFalse(self.matt.is_test)


    def test_status(self):

        # new booking
        book = self.jima.request_booking(when=YESTERDAY, client_ref="Jam2", deadline=YESTERDAY)
        self.assertTrue(book.status, "1")

        book.book(tuner=self.matt)
        self.assertTrue(book.status, "3")

        Booking.check_to_complete()
        self.assertTrue(book.status, "4")


        book.set_complete()
        self.assertTrue(book.status, "5")
        self.assertFalse(book.has_provider_paid)
        self.assertFalse(book.has_client_paid)

        book.set_provider_paid()
        self.assertTrue(book.status, "5")
        self.assertTrue(book.has_provider_paid)
        self.assertFalse(book.has_client_paid)

        book.set_client_paid()
        self.assertTrue(book.status, "9")
        self.assertTrue(book.has_provider_paid)
        self.assertTrue(book.has_client_paid)


        book.client_unpaid()
        self.assertTrue(book.status, "5")
        self.assertTrue(book.has_provider_paid)
        self.assertFalse(book.has_client_paid)

        book.set_provider_unpaid()
        self.assertTrue(book.status, "5")
        self.assertFalse(book.has_provider_paid)
        self.assertFalse(book.has_client_paid)

        book.set_client_paid()
        self.assertTrue(book.status, "5")
        self.assertFalse(book.has_provider_paid)
        self.assertTrue(book.has_client_paid)

        book.set_provider_paid()
        self.assertTrue(book.status, "9")
        self.assertTrue(book.has_provider_paid)
        self.assertTrue(book.has_client_paid)


def roundTime(dt=None, roundTo=60):

   """Round a datetime object to avoid overlaps during testing
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
   """
   tz = timezone.get_current_timezone()
   dt = timezone.make_naive(dt, tz)
   if dt == None :
        return None
   seconds = (dt - dt.min).seconds
   # // is a floor division, not a comment on following line:
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + timedelta(0,rounding-seconds,-dt.microsecond)
