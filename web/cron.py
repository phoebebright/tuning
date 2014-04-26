from django_cron import CronJobBase, Schedule
from web.models import Booking

class CheckBookingStatus(CronJobBase):

    RUN_EVERY_MINS = 5
    MIN_NUM_FAILURES = 3

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'web.check_booking_status'    # a unique code

    def do(self):

        Booking.check_to_complete()
        Booking.delete_temps()

