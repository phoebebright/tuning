from django.conf import settings
from django.contrib.auth.management import create_superuser
from django.contrib.auth import models as auth_app
from django.http import HttpResponse

from django.contrib.auth import get_user_model
User = get_user_model()

from web.models import *


from datetime import datetime, date, timedelta, time


TODAY = date.today()
YESTERDAY = date.today() - timedelta(days = 1)
TOMORROW = date.today() + timedelta(days = 1)
LASTWEEK = date.today() - timedelta(days = 7)
NEXTWEEK = date.today() + timedelta(days = 7)

def test_data(request=None):

    base_data()
    test_bookings()

    return HttpResponse("OK")

def base_data(request=None):

    try:
        Client.objects.get(name="Recording Studio A")
        return
    except Client.DoesNotExist:
        pass

    #activities
    a1 = Activity.objects.create(name="Tuning", name_plural="Tunings", order=0, duration=60)
    a2 = Activity.objects.create(name="Repair", name_plural="Repairs", order=1, duration=120)

    # create organisations
    o1=Client.objects.create(name="Recording Studio A")
    o2=Client.objects.create(name="Recording Studio B")
    o3=Client.objects.create(name="Private House")
    t1=Provider.objects.create(name="Tuner A")
    t2=Provider.objects.create(name="Tuner B")
    t3=Provider.objects.create(name="Tuner C")
    t4=Provider.objects.create(name="Tuner D")
    tstc=Client.objects.create(name="Test Client", test=True)
    tstp=Provider.objects.create(name="Test Provider", test=True)

    # Users
    #su=User.objects.create_superuser('system','system@gmail.com','pass')
    su=User.objects.create_superuser('ajs','phoebebright310+asj@gmail.com','pass')

    u = Booker.objects.create_user('fredA', 'phoebebright310+freda@gmail.com', 'pass')
    u.first_name = "Fred"
    u.last_name = "Smith"
    u.mobile = "123456"
    u.client = o1
    u.save()
    u = Booker.objects.create_user('jimA', 'phoebebright310+jima@gmail.com', 'pass')
    u.first_name = "Jim"
    u.last_name = "Smith"
    u.mobile = "5656564654"
    u.client = o1
    u.save()
    u = Booker.objects.create_user('maryB', 'phoebebright310+maryb@gmail.com', 'pass')
    u.first_name = "Mary"
    u.last_name = "Smith"
    u.mobile = "6756554"
    u.client = o2
    u.save()
    u = Booker.objects.create_user('janePH', 'phoebebright310+janeph@gmail.com', 'pass')
    u.first_name = "Jane"
    u.last_name = "Smith"
    u.mobile = "754456"
    u.client = o3
    u.save()

    u = Tuner.objects.create_user('matt', 'phoebebright310+matt@gmail.com', 'pass')
    u.first_name = "Matt"
    u.last_name = "Apostle"
    u.mobile = "434534534"
    u.provider=t1
    u.score = 10
    u.use_sm = True
    u.save()
    u.activities.add(a1)
    u.activities.add(a2)

    u.save()

    u = Tuner.objects.create_user('luke', 'phoebebright310+luke@gmail.com', 'pass')
    u.first_name = "Luke"
    u.last_name = "Apostle"
    u.mobile = "56756445"
    u.provider=t3
    u.score = 6
    u.use_sm = True
    u.save()
    u.activities.add(a1)
    u.save()

    u = Tuner.objects.create_user('john', 'phoebebright310+john@gmail.com', 'pass')
    u.first_name = "John"
    u.last_name = "Apostle"
    u.mobile = "6764523"
    u.provider=t4
    u.score = 4
    u.save()
    u.activities.add(a2)
    u.save()

    u = Tuner.objects.create_user('mark', 'phoebebright310+mark@gmail.com', 'pass')
    u.first_name = "Mark"
    u.last_name = "Apostle"
    u.mobile = "789876756"
    u.provider=t2
    u.score = 8
    u.save()
    u.activities.add(a1)
    u.activities.add(a2)
    u.save()



    u = Booker.objects.create_user('testera', 'phoebebright310+testa@gmail.com', 'pass')
    u.first_name = "Tester"
    u.last_name = "A"
    u.mobile = "6764523"
    u.client=tstc
    u.save()

    u = Tuner.objects.create_user('testerb', 'phoebebright310+testb@gmail.com', 'pass')
    u.first_name = "Tester"
    u.last_name = "B"
    u.mobile = "6764523"
    u.provider=tstp
    u.score = 2
    u.save()
    u.activities.add(a1)
    u.activities.add(a2)
    u.save()

    u = User.objects.create_user('nobody', 'phoebebright310+nobody@gmail.com', 'pass')
    u.first_name = "Nobody"
    u.last_name = "Nothing"
    u.mobile = "6764523"
    u.save()


    # Studios
    s1 = Studio.objects.create(name="Studio Red", short_code="RED")
    s2 = Studio.objects.create(name="Studio Blue", short_code="BLU")
    s3 = Studio.objects.create(name="Studio Yellow", short_code="YEL")
    s4 = Studio.objects.create(name="Studio Green", short_code="GRN")
    s5 = Studio.objects.create(name="Studio Orange", short_code="ORG")
    s6 = Studio.objects.create(name="Studio 1", short_code="ONE")
    s7 = Studio.objects.create(name="Studio 2", short_code="TWO")
    s8 = Studio.objects.create(name="Test Studio", short_code="TST")

    # Instruments
    Instrument.objects.create(name="Steinway Grand")
    Instrument.objects.create(name="Steinway Upright")
    Instrument.objects.create(name="Fortepiano")
    Instrument.objects.create(name="Harpsicord")
    Instrument.objects.create(name="Grand")
    Instrument.objects.create(name="Upright")
    Instrument.objects.create(name="Test Instrument")


def test_bookings(request=None):

    # don't add twice
    try:
        Booking.objects.get(client_ref="Jam")
        return
    except Booking.DoesNotExist:
        pass


    # get organisations
    o1=Client.objects.get(name="Recording Studio A")
    o2=Client.objects.get(name="Recording Studio B")
    o3=Client.objects.get(name="Private House")
    t1=Provider.objects.get(name="Tuner A")
    t2=Provider.objects.get(name="Tuner B")
    t3=Provider.objects.get(name="Tuner C")
    t4=Provider.objects.get(name="Tuner D")

    #get activities
    a1 = Activity.objects.get(name="Tuning")
    a2 = Activity.objects.get(name="Repair")


    # get users
    freda = Booker.objects.get(username='fredA')
    jima = Booker.objects.get(username='jimA')
    maryb = Booker.objects.get(username='maryB')
    janeph = Booker.objects.get(username='janePH')
    matt = Tuner.objects.get(username='matt')
    mark = Tuner.objects.get(username='mark')
    luke = Tuner.objects.get(username='luke')
    john = Tuner.objects.get(username='john')

    # Studios
    sr = Studio.objects.get(name="Studio Red")
    sb = Studio.objects.get(name="Studio Blue")
    sy = Studio.objects.get(name="Studio Yellow")
    sg = Studio.objects.get(name="Studio Green")
    so = Studio.objects.get(name="Studio Orange")
    s1 = Studio.objects.get(name="Studio 1")
    s2 = Studio.objects.get(name="Studio 2")

    # Instruments
    i1 = Instrument.objects.get(name="Steinway Grand")
    i2 = Instrument.objects.get(name="Steinway Upright")
    i3 = Instrument.objects.get(name="Fortepiano")
    i4 = Instrument.objects.get(name="Harpsicord")
    i5 = Instrument.objects.get(name="Grand")
    i6 = Instrument.objects.get(name="Upright")

    book1 = jima.request_booking(when=TODAY)
    book2 = jima.request_booking(when=TOMORROW, client_ref="Jam", deadline=make_time(TOMORROW, "end"))
    book3 = jima.request_booking(when=(TODAY + timedelta(days = 4)), client_ref="Bono", what=i1, where=sr)
    book3.set_booked(tuner=matt, start_time=datetime.combine(TODAY + timedelta(days = 4), time(16,00)))
    book4 = freda.request_booking(when=(TODAY + timedelta(days = 7)), client_ref="1234", what=i1, where=sr)
    book4.set_booked(tuner=mark, start_time=datetime.combine(TODAY + timedelta(days = 7), time(07,30)))
    book5 = freda.request_booking(when=(TODAY + timedelta(days = 12)), client_ref="NM", what=i2, where=sr)
