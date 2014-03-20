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
    
    
        # get users

        self.freda = User.objects.get(username='fredA')
        self.jima = User.objects.get(username='jimA')
        self.maryb = User.objects.get(username='maryB')
        self.janeph = User.objects.get(username='janePH')
        self.matt = User.objects.get(username='matt')
        self.mark = User.objects.get(username='mark')
        self.luke = User.objects.get(username='luke')
        self.john = User.objects.get(username='john')
    
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

    def test_make_booking(self):


        # test fails

        # can't book in the past

        self.assertRaises(PastDateException, self.freda.request_booking, when=YESTERDAY)
        self.assertRaises(PastDateException, self.freda.request_booking, when=datetime.combine(YESTERDAY, time(12,00)))
        self.assertRaises(PastDateException, self.freda.request_booking,
                          when=datetime.combine(TODAY, time(12,00)),
                          deadline=YESTERDAY)

        #TODO: Test unique ref not being unique - should generate another ref and try again

        # test passes
        book1 = self.freda.request_booking(when=TODAY)
        book1a = Booking.objects.get(id=book1.id)

        # populated fields
        self.assertEqual(book1.status, "asked")
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

    def test_book(self):

        book1 = self.jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
        book1.book(provider=self.matt, start_time=datetime.combine(TOMORROW, time(12,15)))

        self.assertEqual(book1.status, "booked")
        self.assertEqual(book1.provider, self.matt)
        self.assertEqual(roundTime(book1.booked_time, 120), roundTime(datetime.combine(TOMORROW, time(12,15)), 120))  # within 2 seconds
        self.assertEqual(roundTime(book1.booked_at, 120), roundTime(NOW, 120))  # within 2 seconds



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
