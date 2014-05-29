import arrow
from datetime import datetime, date
from dateutil import tz
import pytz

from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
User = get_user_model()

from web.models import *
from web.management.test_data import *
from web.views import *
from django.conf import settings
from libs.utils import make_time, is_list, add_tz

NOW = datetime.now()

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

    # def test_access(self):
    #
    #     # ANYONE - including not logged in
    #
    #     # ADMIN, TUNER OR BOOKER
    #
    #     request = self.factory.get('/bookings/')
    #
    #     # loged in as nobody - not a tuner, booker or admin
    #     request.user = self.nobody
    #
    #     # Test my_view() as if it were deployed at /customer/details
    #     response = bookings_list(request)
    #     self.assertEqual(response.status_code, 200)



    def test_defaults(self):

        # default time for deadline in booking is in settings
        # eg. DEFAULT_DEADLINE_TIME = "09:00"
        # this is in local time so needs to be saved in db as utc

        #http://pytz.sourceforge.net

        settings.DEFAULT_DEADLINE_TIME = "09:00"
        settings.TIME_ZONE = "Europe/London"
        tz = pytz.timezone (settings.TIME_ZONE)

        # test without DST
        local = datetime(2015,2,1,12,0)


        local = tz.localize(local)
        utc = local.astimezone (pytz.utc)

        # in Feb expect local == utc
        self.assertEqual(local, utc)
        self.assertEqual(local.strftime("%H:%M"), utc.strftime("%H:%M"))


         # test with DST
        local = datetime(2015,6,1,12,0)
        local = tz.localize(local)
        utc = local.astimezone (pytz.utc)

        # in June expect local == utc in terms of datetime but not when displayed
        self.assertEqual(local, utc)
        self.assertNotEqual(local.strftime("%H:%M"), utc.strftime("%H:%M"))



        # most of django works on utc (front end on local) but when creating a default
        # deadline, time must converted

        # without DST
        deadline_date = date(2015,2,1)
        deadline_datetime = make_time(datetime(2015,2,1,9,0))
        default  = default_deadline(deadline_date)
        self.assertEqual(default, deadline_datetime)
        self.assertEqual(default.strftime("%H:%M"), "09:00")
        self.assertEqual(default.utcoffset().seconds, 0)

        book1 = self.jima.request_booking(deadline = deadline_date)


        # with DST
        deadline_date = date(2015,6,1)
        deadline_datetime = make_time(datetime(2015,6,1,9,0))
        default  = default_deadline(deadline_date)
        self.assertEqual(default, deadline_datetime)
        self.assertEqual(default.strftime("%H:%M"), "09:00")
        self.assertEqual(default.utcoffset().seconds, 3600)

        book2 = self.jima.request_booking(deadline = deadline_date)


    def test_add_booking(self):

        self.client.login(username=self.maryb.username,password='pass')
        self.client.get("/booking/add/%s/%s/" % (self.o2.id, "201502021400"))
        self.client.get("/booking/add/%s/%s/" % (self.o2.id, "201506021400"))

        bookings = Booking.objects.all()

        book1 = Booking.objects.get(id=1)
        book2 = Booking.objects.get(id=2)

        self.assertEqual(book1.deadline, book2.deadline)
        self.assertNotEqual(book1.deadline.strftime("%H:%M"), book2.deadline.strftime("%H:%M"))
        self.assertEqual(book1.deadline.strftime("%H:%M"), "14:00")
        self.assertEqual(book2.deadline.strftime("%H:%M"), "13:00")

        # local_time_naive = NOW.replace(hour=9).replace(minute=0).replace(second=0)
        # local_time_aware = make_time(local_time_naive)
        # utc_time = make_time(NOW.replace(hour=8).replace(minute=0).replace(second=0))
        #
        # alocal = arrow.now().replace(hour=9, minute=0).to('Europe/London')
        # autc = arrow.now().replace(hour=9, minute=0)
        # anaive = arrow.now().to('Europe/London')
        # a = anaive.to('utc')
        #
        #
        #
        # naive = datetime.strptime ("2014-05-23 09:00:00", "%Y-%m-%d %H:%M:%S")
        # local_dt = local.localize(naive, is_dst=None)
        # utc_dt = local_dt.astimezone (pytz.utc)

        #print local_dt, utc_dt

        # book1 = self.jima.request_booking(deadline = local)
        # self.assertEqual(local, book1.deadline)
        # self.assertEqual(local, book1.requested_to)
        #
        #
        # book2 = self.jima.request_booking(deadline = local)
        #
