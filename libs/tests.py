from django.test import TestCase

from django.conf import settings

from datetime import date, timedelta, time

from libs.utils import *


TODAY = date.today()
YESTERDAY = date.today() - timedelta(days = 1)
TOMORROW = date.today() + timedelta(days = 1)
LASTWEEK = date.today() - timedelta(days = 7)
NEXTWEEK = date.today() + timedelta(days = 7)

class UtilsTest(TestCase):

    from web.models import make_time

    def test_make_time(self):

        dttm = datetime(2014,3,19,0,0)
        dttm_end = datetime(2014,3,19,23,59,59, 999999)
        dt = date(2014,3,19)
        # datetime is unchanged
        self.assertEqual(dttm, make_time(dttm))

        # date to datetime - round up or down
        self.assertEqual(dttm, make_time(dt))
        self.assertEqual(dttm_end, make_time(dt, "end"))

