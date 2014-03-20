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
        Organisation.objects.get(name="Recording Studio A")
        return
    except Organisation.DoesNotExist:
        pass

    # create organisations
    o1=Organisation.objects.create(name="Recording Studio A", org_type="client")
    o2=Organisation.objects.create(name="Recording Studio B", org_type="client")
    o3=Organisation.objects.create(name="Private House", org_type="client")
    t1=Organisation.objects.create(name="Tuner A", org_type="provider")
    t2=Organisation.objects.create(name="Tuner B", org_type="provider")
    t3=Organisation.objects.create(name="Tuner C", org_type="provider")
    t4=Organisation.objects.create(name="Tuner D", org_type="provider")
    s=Organisation.objects.create(name="System", org_type="system")


    # create users
    su=User.objects.create_superuser('system','system@gmail.com','pass')
    su.organisation=s
    su.save()
    u = User.objects.create_user('fredA', 'phoebebright310+freda@gmail.com', 'pass', organisation=o1)
    u.first_name = "Fred"
    u.last_name = "Smith"
    u.mobile = "123456"
    u.save()
    u = User.objects.create_user('jimA', 'phoebebright310+jima@gmail.com', 'pass', organisation=o1)
    u.first_name = "Jim"
    u.last_name = "Smith"
    u.mobile = "5656564654"
    u.save()
    u = User.objects.create_user('maryB', 'phoebebright310+maryb@gmail.com', 'pass', organisation=o2)
    u.first_name = "Mary"
    u.last_name = "Smith"
    u.mobile = "6756554"
    u.save()
    u = User.objects.create_user('janePH', 'phoebebright310+janeph@gmail.com', 'pass', organisation=o3)
    u.first_name = "Jane"
    u.last_name = "Smith"
    u.mobile = "754456"
    u.save()
    u = User.objects.create_user('matt', 'phoebebright310+matt@gmail.com', 'pass', organisation=t1)
    u.first_name = "Matt"
    u.last_name = "Apostle"
    u.mobile = "434534534"
    u.save()
    u = User.objects.create_user('mark', 'phoebebright310+mark@gmail.com', 'pass', organisation=t2)
    u.first_name = "Mark"
    u.last_name = "Apostle"
    u.mobile = "789876756"
    u.save()
    u = User.objects.create_user('luke', 'phoebebright310+luke@gmail.com', 'pass', organisation=t3)
    u.first_name = "Luke"
    u.last_name = "Apostle"
    u.mobile = "56756445"
    u.save()
    u = User.objects.create_user('john', 'phoebebright310+john@gmail.com', 'pass', organisation=t4)
    u.first_name = "John"
    u.last_name = "Apostle"
    u.mobile = "6764523"
    u.save()

    # locations
    Location.objects.create(name="Studio Red", organisation=o1)
    Location.objects.create(name="Studio Blue", organisation=o1)
    Location.objects.create(name="Studio Yellow", organisation=o1)
    Location.objects.create(name="Studio Green", organisation=o1)
    Location.objects.create(name="Studio Orange", organisation=o1)
    Location.objects.create(name="Studio 1", organisation=o2)
    Location.objects.create(name="Studio 2", organisation=o2)

    # Instruments
    Instrument.objects.create(name="Steinway Grand", organisation=o1)
    Instrument.objects.create(name="Steinway Upright", organisation=o1)
    Instrument.objects.create(name="Fortepiano", organisation=o1)
    Instrument.objects.create(name="Harpsicord", organisation=o1)
    Instrument.objects.create(name="Grand", organisation=o2)
    Instrument.objects.create(name="Upright", organisation=o2)


def test_bookings(request=None):

    # don't add twice
    try:
        Booking.objects.get(client_ref="Jam")
        return
    except Booking.DoesNotExist:
        pass


    # get organisations
    o1=Organisation.objects.get(name="Recording Studio A")
    o2=Organisation.objects.get(name="Recording Studio B")
    o3=Organisation.objects.get(name="Private House")
    t1=Organisation.objects.get(name="Tuner A")
    t2=Organisation.objects.get(name="Tuner B")
    t3=Organisation.objects.get(name="Tuner C")
    t4=Organisation.objects.get(name="Tuner D")
    s=Organisation.objects.get(name="System")


    # get users

    freda = User.objects.get(username='fredA')
    jima = User.objects.get(username='jimA')
    maryb = User.objects.get(username='maryB')
    janeph = User.objects.get(username='janePH')
    matt = User.objects.get(username='matt')
    mark = User.objects.get(username='mark')
    luke = User.objects.get(username='luke')
    john = User.objects.get(username='john')

    # locations
    sr = Location.objects.get(name="Studio Red")
    sb = Location.objects.get(name="Studio Blue")
    sy = Location.objects.get(name="Studio Yellow")
    sg = Location.objects.get(name="Studio Green")
    so = Location.objects.get(name="Studio Orange")
    s1 = Location.objects.get(name="Studio 1")
    s2 = Location.objects.get(name="Studio 2")

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
    book3.book(provider=matt, start_time=datetime.combine(TODAY + timedelta(days = 4), time(16,00)))
    book4 = freda.request_booking(when=(TODAY + timedelta(days = 7)), client_ref="1234", what=i1, where=sr)
    book4.book(provider=mark, start_time=datetime.combine(TODAY + timedelta(days = 7), time(07,30)))
    book5 = freda.request_booking(when=(TODAY + timedelta(days = 12)), client_ref="NM", what=i2, where=sr)
