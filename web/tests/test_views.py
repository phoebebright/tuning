
from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
User = get_user_model()

from web.models import *
from web.management.test_data import *
from web.views import *

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



    def test_login(self):


        self.client.login(username='nobody', password='pass')
        response = self.client.get(reverse('bookings_list'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='freda', password='pass')
        response = self.client.get(reverse('bookings_list'))
        self.assertEqual(response.status_code, 200)

        self.client.login(username='luke', password='pass')
        response = self.client.get(reverse('bookings_list'))
        self.assertEqual(response.status_code, 200)

        self.client.login(username='system', password='pass')
        response = self.client.get(reverse('bookings_list'))
        self.assertEqual(response.status_code, 200)