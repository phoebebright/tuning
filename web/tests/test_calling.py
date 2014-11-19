
from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
User = get_user_model()

from web.models import *
from web.management.test_data import *
from web.views import *


from datetime import date, timedelta, time
from django.utils.timezone import utc

from web.tests.tests import list_bookings

NOW = datetime.utcnow().replace(tzinfo=utc)
TODAY = NOW.date()
TODAY_START = make_time(TODAY, "start")
TODAY_END = make_time(TODAY, "end")
YESTERDAY = TODAY - timedelta(days = 1)
TOMORROW = TODAY + timedelta(days = 1)


def list_calls():
    txt = "Calls\n"
    for item in TunerCall.objects.all():
            txt +=  "%s | %s | %s | %s | %s | %s\n" % (item.booking,item.tuner, item.status, item.initiated, item.called, item.answered)

    return txt

class SimpleTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

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
        self.nobody = User.objects.get(username='nobody')

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

    def test_sms_numbers(self):
        """
        test how sms numbers are assigned to each booking
        """

        # no number assigned if booking will not need to send out SMS
        bk1 = Booking.create_booking(self.freda, when=TOMORROW)
        self.assertEqual(bk1.sms_number, None)

        # manually assign a number
        num = bk1.get_sms_number()
        self.assertEqual(bk1.sms_number, num)

        # now release it
        bk1.release_sms_number()
        self.assertEqual(bk1.sms_number, None)

        #bk2 = Booking.create_booking(self.freda, when=TOMORROW)


    def test_calls(self):


        bk1 = Booking.create_booking(self.freda, when=TOMORROW)

        # simeple checks
        call1 = TunerCall.objects.create(booking=bk1)
        self.assertEqual(len(call1.already_called()), 0)
        t1 = call1.get_next_tuner()

        # NO TUNER RESPONDED

        bk2 = Booking.create_booking(self.freda, when=TOMORROW)
        call2 = TunerCall.request(bk2)
        called = call2.already_called()
        self.assertEqual(len(called), 1)
        # know it will be matt has he has highest score
        self.assertEqual(called[0][0], self.matt.id)

        call3 = TunerCall.request(bk2)
        called = call3.already_called()
        self.assertEqual(len(called), 2)
        self.assertIn(((self.matt.id),), called)
        self.assertIn(((self.mark.id),), called)

        TunerCall.request(bk2)
        TunerCall.request(bk2)
        TunerCall.request(bk2)

        # run out of Tuners now
        self.assertRaises(RequestTunerFailed, TunerCall.request, bk2)

        # SECOND TUNER RESPONDED

        bk3 = Booking.create_booking(self.maryb, when=TOMORROW, commit=True)
        self.assertEqual(bk3.status, BOOKING_REQUESTED)

        TunerCall.request(bk3)
        call3 = TunerCall.request(bk3)
        call3.tuner_accepted()

        self.assertEqual(bk3.tuner, call3.tuner)
        self.assertEqual(bk3.status, BOOKING_BOOKED)

        print list_calls()
