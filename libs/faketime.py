from django.conf import settings
import os
import time
from datetime import datetime
import pytz
from django.utils.timezone import utc

#TODO: should handle both tz and niave datetimes - see utils.add_tz

filename = settings.FAKEDATE_FILE

def now():
    if settings.USE_FAKEDATES:
        return getnow()
    else:
        if settings.USE_TZ:
            return datetime.utcnow().replace(tzinfo=utc)
        else:
            return datetime.now()


def setnow(settotime):
        """ Save specified date (not time) in a text file
        """
        f = open(filename, 'w')
        f.write(settotime.strftime('%d/%m/%y'))
        f.close()

def getnow():
    """ get date from text file and add current time to return a datetime object that is offset aware
    """

    try:
        f = open(filename, 'r')
        dt = f.read()
        f.close()
        now =  datetime.combine(datetime.strptime(dt, '%d/%m/%y').date(), datetime.utcnow().replace(tzinfo=utc).time())
    except ValueError:
        setnow(datetime.now())
        now = getnow()



    return now